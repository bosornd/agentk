import asyncio

# pip install fastapi uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse

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

def restaurant_card_message(idx: int) -> str:
    fields = ["id", "name", "address", "stars", "review_count"]
    restaurant = {field: f"{{restaurants[{idx}].{field}}}" for field in fields}

    return json.dumps(format_dict(templates["restaurant_card"], restaurant), ensure_ascii=False)

def state_message(state: dict) -> str:
    return json.dumps({"state": state}, ensure_ascii=False)

def reservation_message() -> str:
    return json.dumps(templates["reservation_state"], ensure_ascii=False)

r1 = restaurant_card_message(0)
r2 = restaurant_card_message(1)
r3 = restaurant_card_message(2)
w = reservation_message()

r = json.dumps({"state": {"restaurants": restaurants}}, ensure_ascii=False)
s1 = json.dumps({"state": {"selected": 0, "status": "생성"}}, ensure_ascii=False)
s2 = json.dumps({"state": {"datetime": "2024-10-10 19:00", "people": 2, "status": "생성"}}, ensure_ascii=False)
s3 = json.dumps({"state": {"datetime": "2024-10-10 19:00", "people": 2, "status": "대기"}}, ensure_ascii=False)
s4 = json.dumps({"state": {"datetime": "2024-10-10 19:00", "people": 2, "status": "확정"}}, ensure_ascii=False)

replies = {
    'r': r, 'r1': r1, 'r2': r2, 'r3': r3,
    'w': w, 's1': s1, 's2': s2, 's3': s3, 's4': s4
}

import uuid

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
        
        reply = replies.get(reply.strip(), reply)
        await message_queues[session_id].put(reply)

    return {"result": "ok"}

@app.get("/stream/{session_id}")
async def stream(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    async def event_generator():
        while True:
            msg = await message_queues[session_id].get()
            yield f"{msg}\n\n"          # "\n\n" is required for SSE

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# FastAPI 실행 명령: uvicorn test_server:app --port 5000 --reload
