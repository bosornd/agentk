# pip install fastapi uvicorn
from fastapi import FastAPI, Request, HTTPException

import asyncio
from fastapi.responses import StreamingResponse
import uuid

app = FastAPI()

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = set()
message_queues = {}

import os
import json

with open(os.path.join(os.path.dirname(__file__), "templates.json"), "r", encoding="utf-8") as f:
    templates = json.load(f)

with open(os.path.join(os.path.dirname(__file__), "restaurants.json"), "r", encoding="utf-8") as f:
    restaurants = json.load(f)

with open(os.path.join(os.path.dirname(__file__), "restaurant_templates.json"), "r", encoding="utf-8") as f:
    restaurant_templates = json.load(f)

def format_dict(d, values):
    if isinstance(d, dict):
        return {k: format_dict(v, values) for k, v in d.items()}
    elif isinstance(d, list):
        return [format_dict(i, values) for i in d]
    elif isinstance(d, str):
        try:
            return d.format(**values)
        except KeyError as e:
            # Replace missing keys with empty string
            class DefaultDict(dict):
                def __missing__(self, key):
                    return ""
            return d.format_map(DefaultDict(values))
    return d

r = json.dumps({"state": {"restaurants": restaurants}}, ensure_ascii=False)
r1 = json.dumps(format_dict(templates["restaurant_card"], restaurant_templates[0]), ensure_ascii=False)
r2 = json.dumps(format_dict(templates["restaurant_card"], restaurant_templates[1]), ensure_ascii=False)
r3 = json.dumps(format_dict(templates["restaurant_card"], restaurant_templates[2]), ensure_ascii=False)

w = json.dumps(templates["reservation_state"], ensure_ascii=False)
s1 = json.dumps({"state": {"selected": 0, "status": "생성"}}, ensure_ascii=False)
s2 = json.dumps({"state": {"datetime": "2024-10-10 19:00", "people": 2, "status": "생성"}}, ensure_ascii=False)
s3 = json.dumps({"state": {"datetime": "2024-10-10 19:00", "people": 2, "status": "대기"}}, ensure_ascii=False)
s4 = json.dumps({"state": {"datetime": "2024-10-10 19:00", "people": 2, "status": "확정"}}, ensure_ascii=False)

@app.post("/session")           # localhost:5000/session
async def create_session():
    session_id = str(uuid.uuid4())
    sessions.add(session_id)
    message_queues[session_id] = asyncio.Queue()
    return {"session_id": session_id}

@app.post("/chat")              # localhost:5000/chat
async def chat(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    user_message = data.get("text", "")

    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    print(f"[{session_id}] User: {user_message}")
    print(f"[{session_id}] Agent: (여러 줄 입력, 빈 줄 입력 시 종료)")
    while True:
        reply = input()
        if reply.strip() == '':
            break
        elif reply.strip() == 'r': reply = r
        elif reply.strip() == 'r1': reply = r1
        elif reply.strip() == 'r2': reply = r2
        elif reply.strip() == 'r3': reply = r3
        elif reply.strip() == 'w': reply = w
        elif reply.strip() == 's1': reply = s1
        elif reply.strip() == 's2': reply = s2
        elif reply.strip() == 's3': reply = s3
        elif reply.strip() == 's4': reply = s4

        await message_queues[session_id].put(reply)

    return {"result": "ok"}

@app.get("/stream/{session_id}")
async def stream(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    async def event_generator():
        while True:
            msg = await message_queues[session_id].get()
            yield f"{msg}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# FastAPI 실행 명령: uvicorn test_server:app --host 0.0.0.0 --port 5000
