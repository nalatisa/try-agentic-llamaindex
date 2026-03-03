from dotenv import load_dotenv

load_dotenv()

import asyncio
import json
import logging

import requests
from llama_index.core.agent import AgentWorkflow, FunctionAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.google_genai import GoogleGenAI

# LOGGING (DEBUG MODE AKTIF)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("llama_index").setLevel(logging.DEBUG)


# Import validator Pydantic
try:
    from models import IRQuery
except ImportError:
    print("Warning: models.py tidak ditemukan → validasi Pydantic dilewati.")
    IRQuery = None


# SETUP LLM GEMINI
llm = GoogleGenAI(
    model="gemini-2.5-flash",
    temperature=0.0,
)


# TOOL: Fetch schema dari dummy API
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


# SYSTEM PROMPT
try:
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()
except FileNotFoundError:
    print("Warning: system_prompt.txt tidak ditemukan!")
    system_prompt = "You are a helpful assistant that outputs only valid JSON IR query."


# AGENT SETUP (VERBOSE AKTIF)
agent = FunctionAgent(
    llm=llm,
    tools=[fetch_schema_tool],
    system_prompt=system_prompt,
    verbose=True,  # ⬅️ penting buat lihat reasoning loop
    output_cls=IRQuery,
)

workflow = AgentWorkflow(agents=[agent])


# MAIN LOOP – TERMINAL CHAT
async def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║ Semesta IR Builder Agent – Gemini 2.5 Flash (DEBUG MODE)   ║")
    print("║                                                            ║")
    print("║ Ketik 'exit', 'keluar', 'quit', 'q' untuk berhenti         ║")
    print("╚════════════════════════════════════════════════════════════╝")

    while True:
        user_input = input("\nQuery kamu: ").strip()

        if user_input.lower() in ["exit", "keluar", "quit", "q"]:
            print("\nTerima kasih!")
            break

        if not user_input:
            print("Masukkan query.")
            continue

        print("\nAgent sedang memproses...\n")

        try:
            result = await workflow.run(user_msg=user_input)

            print("\nRAW RESULT OBJECT:")
            print(result)
            print()

            if (
                IRQuery is not None
                and hasattr(result, "response")
                and isinstance(result.response, IRQuery)
            ):
                ir_obj = result.response
                output_json = ir_obj.model_dump_json(indent=2)

                print("═" * 90)
                print("JSON IR VALID (Pydantic validated):")
                print(output_json)
                print("═" * 90)

            else:
                output = ""
                if hasattr(result, "content"):
                    output = result.content or ""
                elif hasattr(result, "message") and hasattr(result.message, "content"):
                    output = result.message.content or ""
                else:
                    output = str(result)

                output = output.strip()

                if output.startswith("```json"):
                    output = output[7:].lstrip()
                if output.endswith("```"):
                    output = output[:-3].rstrip()

                print("═" * 90)
                print("⚠️ Hasil fallback (bukan objek IRQuery):")
                print(output)
                print("═" * 90)

        except Exception as e:
            print(f"\n❌ Terjadi error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
