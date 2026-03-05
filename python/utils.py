# utils.py
# helper function

import json
import re

from agents import classifier_workflow


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
# DEEP MERGE
# =============================
def deep_merge(base: dict, changes: dict) -> dict:
    for key, value in changes.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base


# # =============================
# # DIFF PATCHER (SIMPLE)
# # =============================
# def apply_simple_json_diff(current_json: dict, diff_text: str) -> dict:
#     lines = diff_text.splitlines()

#     for line in lines:
#         if line.startswith("+") and not line.startswith("+++"):
#             new_line = line[1:].strip().rstrip(",")

#             match = re.match(r'"(.+?)"\s*:\s*(.+)', new_line)
#             if match:
#                 key = match.group(1)
#                 value_raw = match.group(2)

#                 try:
#                     value = json.loads(value_raw)
#                 except:
#                     value = value_raw.strip('"')

#                 current_json[key] = value

#     return current_json
