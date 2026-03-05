run dummy data: uvicorn dummy_api:app --reload port 8001
run agent: uvicorn api:app --reload --port 8000
run chainlit ui: chainlit run ui.py --port 8002
