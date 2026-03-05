# main.py
import asyncio
import json
import logging

from core import process_query

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("llama_index").setLevel(logging.DEBUG)

# STATE
current_ir = None
ir_history = []


# =============================
# MAIN LOOP
# =============================
async def main():
    global current_ir
    print("╔════════════╗")
    print("║ IR Builder ║")
    print("╚════════════╝")

    while True:
        user_input = input("\nQuery: ").strip()
        if user_input.lower() in ["exit", "quit", "q"]:
            print("\nSelesai.")
            break

        if user_input.lower() == "reset":
            current_ir = None
            ir_history.clear()
            print("IR state direset.")
            continue

        if user_input.lower() == "history":
            print("\n=== IR HISTORY ===")
            for idx, ir in enumerate(ir_history):
                print(f"\n[{idx}]")
                print(json.dumps(ir, indent=2))
            print("\nCurrent IR:")
            print(json.dumps(current_ir, indent=2) if current_ir else "None")
            continue

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
            # Panggil fungsi dari core.py
            updated_ir, updated_history = await process_query(
                user_input, current_ir, ir_history
            )

            # Update state di main.py
            current_ir = updated_ir
            ir_history[:] = updated_history  # update list

        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
