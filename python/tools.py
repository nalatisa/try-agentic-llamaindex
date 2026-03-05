# tools.py
# tool yang digunain agents

import requests
from config import SCHEMA_BASE_URL
from llama_index.core.tools import FunctionTool


def fetch_dwh_schema(source_id: str) -> str:
    print(f"\n TOOL DIPANGGIL source_id={source_id}\n")
    try:
        url = f"{SCHEMA_BASE_URL}/schema?source_id={source_id}"

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
