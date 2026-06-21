import os
import logging
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from app.app_utils.telemetry import setup_telemetry
from app.expense_agent.agent import root_agent

load_dotenv()

# Setup standard Python logging for console logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ambient-expense-agent")

# Telemetry: Using default config. Ensure otel_to_cloud=False conceptually.
# We are no longer passing otel_to_cloud=True to get_fast_api_app.
setup_telemetry()

app = FastAPI(
    title="ambient-expense-agent", 
    description="Ambient API for interacting with the expense agent via Pub/Sub"
)

# SQLite persistent storage to share sessions with Dev UI
session_service = DatabaseSessionService(db_url="sqlite+aiosqlite:///sessions.db")

@app.post("/")
async def pubsub_trigger(request: Request):
    """Accepts Pub/Sub push messages and feeds them into the workflow."""
    envelope = await request.json()
    if not envelope:
        return {"status": "error", "message": "No Pub/Sub message received"}
        
    subscription = envelope.get("subscription", "")
    
    # Normalize the fully-qualified subscription path to a short name to keep session records readable
    session_id = subscription.split("/")[-1] if "/" in subscription else subscription
    if not session_id:
        session_id = "default-session"
        
    logger.info(f"Received Pub/Sub event for session: {session_id}")
    
    data = envelope.get("message", {}).get("data", "")
    
    # Pack the raw data into a Content object for the workflow's START node
    message = types.Content(role="user", parts=[types.Part.from_text(text=data)])
    
    try:
        # Create session if it doesn't exist
        try:
            await session_service.create_session(app_name="app", user_id="ambient-user", session_id=session_id)
        except Exception:
            pass # Session might already exist
            
        runner = Runner(agent=root_agent, app_name="app", session_service=session_service)
            
        # Feed the message into the workflow
        async for event in runner.run_async(user_id="ambient-user", session_id=session_id, new_message=message):
            if event.output is not None:
                logger.info(f"Workflow produced output: {event.output}")
                
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {"status": "error", "message": str(e)}

# Main execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
