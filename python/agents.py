# agents.py
from config import classifier_system_prompt, edit_system_prompt, llm, system_prompt
from llama_index.core.agent import AgentWorkflow, FunctionAgent
from tools import fetch_schema_tool

# load ir model
try:
    from models import IRQuery
except ImportError:
    print("Warning: models.py tidak ditemukan → validasi Pydantic dilewati.")
    IRQuery = None

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
