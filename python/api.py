# api.py

import json

from core import process_query_stream
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

current_ir = None
ir_history = []


class QueryRequest(BaseModel):
    query: str


async def event_stream(query: str):
    global current_ir, ir_history

    async for chunk in process_query_stream(query, current_ir, ir_history):
        if chunk["type"] == "result":
            current_ir = chunk["current_ir"]
            ir_history = chunk["history"]

        yield f"data: {json.dumps(chunk)}\n\n"


@app.post("/query")
async def query(req: QueryRequest):
    return StreamingResponse(
        event_stream(req.query),
        media_type="text/event-stream",
    )
