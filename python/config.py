# config.py
# konfigurasi llm, data tools, dan prompts

import os

from dotenv import load_dotenv
from llama_index.llms.google_genai import GoogleGenAI

load_dotenv()

# konifgurasi llm
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = GoogleGenAI(
    model="gemini-2.5-flash",
    temperature=0.0,
    api_key=GEMINI_API_KEY,
)

# konfigurasi tools
SCHEMA_BASE_URL = os.getenv("SCHEMA_BASE_URL")

# konfigurasi prompts
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

system_prompt_path = os.path.join(PROJECT_ROOT, "prompts", "system_prompt.txt")
edit_system_prompt_path = os.path.join(
    PROJECT_ROOT, "prompts", "edit_system_prompt.txt"
)
classifier_system_prompt_path = os.path.join(
    PROJECT_ROOT, "prompts", "classifier_system_prompt.txt"
)

try:
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()
except FileNotFoundError:
    system_prompt = """
You are an IR builder.
Return ONLY raw JSON.
Do NOT wrap in markdown.
Do NOT use ```json.
"""

try:
    with open(edit_system_prompt_path, "r", encoding="utf-8") as f:
        edit_system_prompt = f.read().strip()
except FileNotFoundError:
    edit_system_prompt = """
You are an IR semantic editor.
Your job: Return ONLY a JSON object containing ONLY the fields that must change.
Return ONLY the JSON patch.
"""

try:
    with open(classifier_system_prompt_path, "r", encoding="utf-8") as f:
        classifier_system_prompt = f.read().strip()
except FileNotFoundError:
    classifier_system_prompt = """
You are an IR intent classifier.
You must classify the user request into one of:
- NEW → completely new query unrelated to previous IR.
- MODIFY_LAST → modification of the most recent IR.
- MODIFY_REFERENCE → modification of a previous IR that is not the latest one.

Return STRICT JSON:
{
    "mode": "...",
    "target_index": number or null
}
"""
