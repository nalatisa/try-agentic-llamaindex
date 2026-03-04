from dotenv import load_dotenv

load_dotenv()

import asyncio
import json
import logging
import re

import requests
from llama_index.core.agent import AgentWorkflow, FunctionAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.google_genai import GoogleGenAI

# =============================
# LOGGING
# =============================
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("llama_index").setLevel(logging.DEBUG)

# =============================
# GLOBAL STATE
# =============================
# biar tau ir json terakhir (biar bisa dimodifikasi)
current_ir = None
# simpan sementara seluruh ir, biar bisa pilih ir mana yang mau dimodifikasi
ir_history = []

# =============================
# LOAD IR MODEL
# =============================
# cek apakah ir udah sesuai json apa belum
try:
    from models import IRQuery
except ImportError:
    print("Warning: models.py tidak ditemukan → validasi Pydantic dilewati.")
    IRQuery = None


# =============================
# LLM SETUP
# =============================
llm = GoogleGenAI(
    model="gemini-2.5-flash",
    temperature=0.0,
)


# =============================
# TOOL: FETCH SCHEMA
# =============================
def fetch_dwh_schema(source_id: str) -> str:
    print(f"\n TOOL DIPANGGIL source_id={source_id}\n")

    try:
        url = f"http://127.0.0.1:8001/schema?source_id={source_id}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            return f"Error dari API: {data['error']}"

        tables_str = "\n".join(
            [
                f"Table: {t['name']}\nKolom:\n"
                + "\n".join(f" - {c['name']} ({c['type']})" for c in t["columns"])
                for t in data.get("tables", [])
            ]
        )

        return (
            f"Schema source_id: {data['source_id']} ({data['provider']})\n\n"
            f"Tabel tersedia:\n{tables_str}\n\n"
            "Gunakan hanya tabel & kolom di atas."
        )

    except Exception as e:
        return f"Gagal ambil schema: {str(e)}. Gunakan info dari prompt saja."


fetch_schema_tool = FunctionTool.from_defaults(fn=fetch_dwh_schema)


# =============================
# LOAD PROMPTS
# =============================
# system prompt utama untuk ngeluarin output json
try:
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()
except FileNotFoundError:
    system_prompt = """
You are an IR builder.

Return ONLY raw JSON.
Do NOT wrap in markdown.
Do NOT use ```json.
"""

# system prompt untuk mengedit bagian dari json, sesuai permintaan
try:
    with open("edit_system_prompt.txt", "r", encoding="utf-8") as f:
        edit_system_prompt = f.read().strip()
except FileNotFoundError:
    edit_system_prompt = """
You are an IR diff editor.

Return ONLY unified diff.
Do NOT wrap in markdown.
"""

# system prompt untuk cek apakah ini perintah baru atau perintah sebelumnya yang bisa dimodifikasi
try:
    with open("classifier_system_prompt.txt", "r", encoding="utf-8") as f:
        classifier_system_prompt = f.read().strip()
except FileNotFoundError:
    classifier_system_prompt = """
You are a query intent classifier.

Return ONLY:
NEW
or
MODIFY
"""


# =============================
# AGENTS
# =============================

# agent utama ambil data
agent = FunctionAgent(
    llm=llm,
    tools=[fetch_schema_tool],
    system_prompt=system_prompt,
    verbose=True,
    output_cls=IRQuery,
)

workflow = AgentWorkflow(agents=[agent])

# agent untuk edit system prompt
edit_agent = FunctionAgent(
    llm=llm,
    system_prompt=edit_system_prompt,
    verbose=True,
)

edit_workflow = AgentWorkflow(agents=[edit_agent])

# agent untuk klasifikasi ini permintaan baru atau lama
classifier_agent = FunctionAgent(
    llm=llm,
    system_prompt=classifier_system_prompt,
    verbose=False,
)

classifier_workflow = AgentWorkflow(agents=[classifier_agent])


# =============================
# CLEAN JSON HELPER
# =============================
def clean_json_output(text: str) -> str:
    text = text.strip()

    # Remove ```json or ``` wrappers
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)

    return text.strip()


# =============================
# CLASSIFY INTENT FUNCTION
# =============================
async def classify_intent(user_input: str) -> dict:
    # Buat ringkasan history (cukup tabel + limit)
    history_summary = []

    for idx, ir in enumerate(ir_history):
        table = ir.get("from", {}).get("table")
        limit = ir.get("limit")
        history_summary.append({"index": idx, "table": table, "limit": limit})

    last_ir_summary = None
    if current_ir:
        last_ir_summary = {
            "table": current_ir.get("from", {}).get("table"),
            "limit": current_ir.get("limit"),
        }

    classifier_prompt = f"""
IR History:
{json.dumps(history_summary, indent=2)}

Last IR:
{json.dumps(last_ir_summary, indent=2)}

User Query:
{user_input}
"""

    result = await classifier_workflow.run(user_msg=classifier_prompt)

    raw_output = ""
    if hasattr(result, "content"):
        raw_output = result.content.strip()
    else:
        raw_output = str(result).strip()

    cleaned = clean_json_output(raw_output)

    try:
        return json.loads(cleaned)
    except:
        return {"mode": "NEW", "target_index": None}


# =============================
# DIFF PATCHER (SIMPLE)
# =============================
def apply_simple_json_diff(current_json: dict, diff_text: str) -> dict:
    lines = diff_text.splitlines()

    for line in lines:
        if line.startswith("+") and not line.startswith("+++"):
            new_line = line[1:].strip().rstrip(",")

            match = re.match(r'"(.+?)"\s*:\s*(.+)', new_line)
            if match:
                key = match.group(1)
                value_raw = match.group(2)

                try:
                    value = json.loads(value_raw)
                except:
                    value = value_raw.strip('"')

                current_json[key] = value

    return current_json


# =============================
# MAIN LOOP
# =============================
async def main():
    global current_ir

    print("╔════════════════════════════════════════════════════╗")
    print("║ IR Builder                                         ║")
    print("╚════════════════════════════════════════════════════╝")

    while True:
        user_input = input("\nQuery: ").strip()

        if user_input.lower() in ["exit", "quit", "q"]:
            print("\nSelesai.")
            break

        if user_input.lower() == "reset":
            current_ir = None
            print("IR state direset.")
            continue

        # =============================
        # COMMAND: SHOW HISTORY
        # =============================
        if user_input.lower() == "history":
            print("\n=== IR HISTORY ===")
            for idx, ir in enumerate(ir_history):
                print(f"\n[{idx}]")
                print(json.dumps(ir, indent=2))
            print("\nCurrent IR:")
            print(json.dumps(current_ir, indent=2) if current_ir else "None")
            continue

        # =============================
        # COMMAND: UNDO
        # =============================
        if user_input.lower() == "undo":
            if ir_history:
                current_ir = ir_history.pop()
                print("\n↩️ Reverted to previous IR:")
                print(json.dumps(current_ir, indent=2))
            else:
                print("History kosong.")
            continue

        if not user_input:
            continue

        print("\nAgent sedang memproses...\n")

        try:
            # =============================
            # INTENT CLASSIFICATION
            # =============================
            intent_data = {"mode": "NEW", "target_index": None}

            if current_ir is not None:
                intent_data = await classify_intent(user_input)
                print(f"[Intent detected: {intent_data}]")

            mode = intent_data.get("mode", "NEW")
            target_index = intent_data.get("target_index")

            # =============================
            # MODE 1 – GENERATE IR
            # =============================
            if current_ir is None or mode == "NEW":
                result = await workflow.run(user_msg=user_input)

                # Ambil raw text
                raw_output = ""
                if hasattr(result, "content"):
                    raw_output = result.content or ""
                elif hasattr(result, "message") and hasattr(result.message, "content"):
                    raw_output = result.message.content or ""
                else:
                    raw_output = str(result)

                cleaned = clean_json_output(raw_output)

                try:
                    parsed_json = json.loads(cleaned)

                    if current_ir is not None:
                        ir_history.append(current_ir)

                    current_ir = parsed_json

                    print("═" * 80)
                    print("IR DISIMPAN:")
                    print(json.dumps(current_ir, indent=2))
                    print("═" * 80)

                except Exception as e:
                    print("❌ Gagal parse JSON:")
                    print(cleaned)
                    print("Error:", e)

            # =============================
            # MODE 2 – EDIT IR (DIFF)
            # =============================
            else:
                # Tentukan IR dasar
                base_ir = current_ir

                if mode == "MODIFY_REFERENCE":
                    if isinstance(target_index, int) and 0 <= target_index < len(
                        ir_history
                    ):
                        base_ir = ir_history[target_index]
                        print(f"[Menggunakan IR index {target_index} sebagai base]")
                    else:
                        print("[Index tidak valid → fallback ke current_ir]")

                edit_prompt = f"""
            Current IR:
            {json.dumps(base_ir, indent=2)}

            User modification request:
            {user_input}
            """

                diff_result = await edit_workflow.run(user_msg=edit_prompt)

                raw_diff = ""
                if hasattr(diff_result, "content"):
                    raw_diff = diff_result.content or ""
                else:
                    raw_diff = str(diff_result)

                cleaned_diff = clean_json_output(raw_diff)

                print("═" * 80)
                print("DIFF DITERIMA:")
                print(cleaned_diff)
                print("═" * 80)

                ir_history.append(current_ir.copy())
                current_ir = apply_simple_json_diff(base_ir.copy(), cleaned_diff)

                print("═" * 80)
                print("IR UPDATED:")
                print(json.dumps(current_ir, indent=2))
                print("═" * 80)

        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
