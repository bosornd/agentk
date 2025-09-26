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

import os
import json

with open(os.path.join(os.path.dirname(__file__), "templates.json"), "r", encoding="utf-8") as f:
    templates = json.load(f)

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

import uuid
import httpx

async def _create_session():
    session_id = str(uuid.uuid4())
    url = "http://localhost:8000/apps/agent/users/user1/sessions/" + session_id
    payload = {
        "restaurants": "",
        "reservation": ""
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        session_id = data.get("id", session_id)

    return session_id

async def _invoke_agent(session_id: str, user_message: str) -> dict:
    url = "http://localhost:8000/run"
    payload = {
        "app_name": "agent",
        "user_id": "user1",
        "session_id": session_id,
        "new_message": { "role": "user", "parts": [{ "text": user_message }] },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        return data[-1]["actions"]["stateDelta"]
    
sessions = set()
message_queues = {}
restaurants = {}
reservation = {}

@app.post("/session")           # localhost:5000/session
async def create_session():
    session_id = await _create_session()

    sessions.add(session_id)
    message_queues[session_id] = asyncio.Queue()

    return {"session_id": session_id}

@app.post("/chat")              # localhost:5000/chat
async def chat(request: Request):
    data = await request.json()
    session_id = data.get("session_id")

    if "text" in data and data["text"].strip():
        user_message = data["text"]
        print(f"[{session_id}] User: {user_message}")

        if not session_id or session_id not in sessions:
            raise HTTPException(status_code=400, detail="Invalid session_id")
        
        state_delta = await _invoke_agent(session_id, user_message)
        print(f"[{session_id}] Agent: {state_delta}")

        if "restaurants" in state_delta:
            length = len(restaurants[session_id]) if session_id in restaurants else 0

            await message_queues[session_id].put(state_message(state_delta["restaurants"]))

            for idx in range(length, len(state_delta["restaurants"]["restaurants"])):
                await message_queues[session_id].put(restaurant_card_message(idx))

            restaurants[session_id] = state_delta["restaurants"]["restaurants"]

        if "reservation" in state_delta:
            if session_id not in reservation:
                await message_queues[session_id].put(reservation_message())

            state_delta["reservation"]["selected"] = state_delta["reservation"]["selected"] - 1

            await message_queues[session_id].put(state_message(state_delta["reservation"]))
            reservation[session_id] = state_delta["reservation"]
    else:
        await message_queues[session_id].put("무엇을 도와드릴까요?")

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

# FastAPI 실행 명령: uvicorn server:app --port 5000 --reload
