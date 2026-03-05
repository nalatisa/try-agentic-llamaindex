# python/core.py
import json

from agents import classifier_workflow, edit_workflow, workflow
from utils import clean_json_output, deep_merge


# classify intent
async def classify_intent(user_input: str, current_ir, ir_history) -> dict:
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
    except (json.JSONDecodeError, TypeError):
        return {"mode": "NEW", "target_index": None}


async def process_query(user_input: str, current_ir, ir_history):
    #  return tuple (updated_ir, updated_history) supaya main.py bisa update state
    intent_data = {"mode": "NEW", "target_index": None}
    if current_ir is not None:
        intent_data = await classify_intent(user_input, current_ir, ir_history)
        print(f"[Intent detected: {intent_data}]")

    mode = intent_data.get("mode", "NEW")
    target_index = intent_data.get("target_index")

    # =============================
    # MODE 1 – GENERATE IR
    # =============================
    if current_ir is None or mode == "NEW":
        result = await workflow.run(user_msg=user_input)
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
        return current_ir, ir_history

        # =============================
        # MODE 2 – EDIT IR (SEMANTIC)
        # =============================
    else:
        base_ir = current_ir
        if mode == "MODIFY_REFERENCE":
            if isinstance(target_index, int) and 0 <= target_index < len(ir_history):
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
        edit_result = await edit_workflow.run(user_msg=edit_prompt)
        raw_output = ""
        if hasattr(edit_result, "content"):
            raw_output = edit_result.content or ""
        else:
            raw_output = str(edit_result)
        cleaned = clean_json_output(raw_output)
        print("═" * 80)
        print("SEMANTIC PATCH DITERIMA:")
        print(cleaned)
        print("═" * 80)
        try:
            changes = json.loads(cleaned)
            ir_history.append(current_ir.copy())
            current_ir = deep_merge(base_ir.copy(), changes)
            print("═" * 80)
            print("IR UPDATED:")
            print(json.dumps(current_ir, indent=2))
            print("═" * 80)
        except Exception as e:
            print("❌ Gagal parse semantic edit JSON:")
            print(cleaned)
            print("Error:", e)
        return current_ir, ir_history

        # # =============================
        # # MODE 2 – EDIT IR (DIFF)
        # # =============================
        # else:
        #     # Tentukan IR dasar
        #     base_ir = current_ir

        #     if mode == "MODIFY_REFERENCE":
        #         if isinstance(target_index, int) and 0 <= target_index < len(
        #             ir_history
        #         ):
        #             base_ir = ir_history[target_index]
        #             print(f"[Menggunakan IR index {target_index} sebagai base]")
        #         else:
        #             print("[Index tidak valid → fallback ke current_ir]")

        #     edit_prompt = f"""
        # Current IR:
        # {json.dumps(base_ir, indent=2)}

        # User modification request:
        # {user_input}
        # """

        #     diff_result = await edit_workflow.run(user_msg=edit_prompt)

        #     raw_diff = ""
        #     if hasattr(diff_result, "content"):
        #         raw_diff = diff_result.content or ""
        #     else:
        #         raw_diff = str(diff_result)

        #     cleaned_diff = clean_json_output(raw_diff)

        #     print("═" * 80)
        #     print("DIFF DITERIMA:")
        #     print(cleaned_diff)
        #     print("═" * 80)

        #     ir_history.append(current_ir.copy())
        #     current_ir = apply_simple_json_diff(base_ir.copy(), cleaned_diff)

        #     print("═" * 80)
        #     print("IR UPDATED:")
        #     print(json.dumps(current_ir, indent=2))
        #     print("═" * 80)


# streaming
async def process_query_stream(user_input: str, current_ir, ir_history):
    yield {"type": "status", "message": "Memproses intent..."}

    intent_data = {"mode": "NEW", "target_index": None}
    if current_ir is not None:
        intent_data = await classify_intent(user_input, current_ir, ir_history)
        yield {"type": "intent", "data": intent_data}

    yield {"type": "status", "message": "Menjalankan workflow..."}

    updated_ir, updated_history = await process_query(
        user_input, current_ir, ir_history
    )

    yield {
        "type": "result",
        "current_ir": updated_ir,
        "history": updated_history,
    }
