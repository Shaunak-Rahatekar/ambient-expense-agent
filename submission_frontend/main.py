import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService
import vertexai

app = FastAPI()

templates = Jinja2Templates(directory="templates")

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "ambient-expense-agent-500111")
AGENT_RUNTIME_ID = os.environ.get("AGENT_RUNTIME_ID")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east1")

vertexai.init(project=PROJECT_ID, location=LOCATION)
session_service = VertexAiSessionService(
    project=PROJECT_ID,
    location=LOCATION
)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/pending")
async def pending_approvals():
    if not AGENT_RUNTIME_ID:
        return {"error": "AGENT_RUNTIME_ID not set"}
    
    pending = []
    
    for uid in ["default-user", "vais-query-reasoning-engine"]:
        response = await session_service.list_sessions(app_name=AGENT_RUNTIME_ID, user_id=uid)
        
        for sess in response.sessions:
            full_session = await session_service.get_session(
                app_name=AGENT_RUNTIME_ID, 
                user_id=uid, 
                session_id=sess.id
            )
            if not full_session or not full_session.events:
                continue
                
            # Find unresolved adk_request_input events
            requested_inputs = {} # id -> event
            responses = set()
            
            for event in full_session.events:
                if not event.content or not event.content.parts:
                    continue
                for part in event.content.parts:
                    if getattr(part, 'function_call', None) and part.function_call.name == 'adk_request_input':
                        requested_inputs[part.function_call.id] = part.function_call
                        
                    if getattr(part, 'function_response', None) and part.function_response.name == 'adk_request_input':
                        responses.add(part.function_response.id)
                        
            for req_id, call in requested_inputs.items():
                if req_id not in responses:
                    # Unresolved! Get the arguments which should contain the expense payload.
                    try:
                        args = dict(call.args) if call.args else {}
                    except Exception:
                        args = {}
                    pending.append({
                        "session_id": sess.id,
                        "user_id": uid,
                        "interrupt_id": req_id,
                        "payload": args
                    })
                
    return {"pending": pending}

@app.post("/api/action/{session_id}")
async def action(session_id: str, request: Request):
    data = await request.json()
    interrupt_id = data.get("interrupt_id")
    user_id = data.get("user_id", "default-user")
    approved = data.get("approved", False)
    
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
    agent = client.agent_engines.get(name=AGENT_RUNTIME_ID)
    
    # Resume payload directly to message
    resume_payload = {
        "role": "user",
        "parts": [{
            "function_response": {
                "id": interrupt_id,
                "name": "adk_request_input",
                "response": {"output": "approve" if approved else "reject"}
            }
        }]
    }
    
    # Send it to the agent synchronously using .query()
    agent.query(message=resume_payload, user_id=user_id, session_id=session_id)
        
    return {"status": "success", "approved": approved}
