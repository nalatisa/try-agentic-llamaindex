# chainlit ui
import json

import chainlit as cl
import requests

API_URL = "http://localhost:8000/query"


@cl.on_message
async def main(message: cl.Message):

    with requests.post(
        API_URL,
        json={"query": message.content},
        stream=True,
    ) as r:
        msg = cl.Message(content="Processing...")
        await msg.send()

        for line in r.iter_lines():
            if not line:
                continue

            if line.startswith(b"data:"):
                data = json.loads(line[5:])

                if data["type"] == "status":
                    msg.content = data["message"]
                    await msg.update()

                elif data["type"] == "intent":
                    msg.content = f"Intent detected: {data['data']}"
                    await msg.update()

                elif data["type"] == "result":
                    ir_json = json.dumps(data["current_ir"], indent=2)

                    msg.content = (
                        "IR Result\n\n```json\n" + ir_json + "\n```"
                    )  # biar json bisa dicopas
                    await msg.update()
