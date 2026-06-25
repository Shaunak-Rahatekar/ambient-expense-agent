import vertexai
from vertexai.preview import reasoning_engines
import requests
import time

def test_human_in_loop():
    print("=== Initializing ===")
    vertexai.init(project="ambient-expense-agent-500111", location="us-east1")
    agent_id = "projects/1042866970340/locations/us-east1/reasoningEngines/2994999305317646336"
    agent = reasoning_engines.ReasoningEngine(agent_id)

    # Use a unique session ID for this test
    session_id = f"test-session-{int(time.time())}"
    
    # 1. Submit a risky expense
    payload = '{"id": "EXP-101", "amount": 5000, "description": "Client dinner", "date": "2026-06-04", "submitter": "Alice", "employee_name": "Alice Smith", "merchant": "Steakhouse", "category": "Meals"}'

    print(f"\n=== Step 1: Submitting risky expense to session {session_id} ===")
    response_iterator = agent.query(
        message=payload, 
        user_id="default-user", 
        session_id=session_id
    )
    
    events = list(response_iterator)
    print(f"Response from Cloud (Empty means agent paused): {events}")

    # 2. Simulate Frontend fetching the pending session to get the function call ID
    print("\n=== Step 2: Fetching pending sessions to find function call ID ===")
    time.sleep(2) # Give it a moment to persist
    
    # Fetch from your dashboard API
    api_url = "https://expense-manager-dashboard-4tisa46mxq-ue.a.run.app/api/pending"
    print(f"Fetching from {api_url}...")
    try:
        response = requests.get(api_url)
        pending_sessions = response.json().get("pending", [])
    except Exception as e:
        print(f"Failed to fetch pending sessions: {e}")
        return

    # Find our specific session
    my_pending_session = next((s for s in pending_sessions if s.get("session_id") == session_id), None)
    
    if not my_pending_session:
        print(f"Could not find session {session_id} in pending list! It may not have paused.")
        return
        
    print(f"Found pending session! Waiting for human approval on expense: {my_pending_session.get('payload', {}).get('payload')}")
    
    # We need the actual function call ID to resume. The frontend API might abstract it, 
    # but the proper payload requires the ID. 
    # For this test, we'll assume we can get it or we'll just format the payload correctly.
    # To keep it simple, we'll demonstrate the structure:
    
    print("\n=== Step 3: Resuming workflow ===")
    decision = "approve"
    print(f"Simulating human decision: {decision}")
    
    # NOTE: To programmatically resume in ADK, we format the message as a FunctionResponse.
    # The ID must match the functionCall ID that the agent emitted. 
    # For demonstration, we'll send it back as a generic message since `agent_runtime_app.py` 
    # requires exact IDs which the frontend API doesn't expose yet.
    
    # However, if using the Playground UI, it automatically handles this parsing!
    print("If you use the Playground UI, you just type 'approve' and it automatically constructs the FunctionResponse.")
    print("For a programmatic client, you would send a FunctionResponse payload to the session.")

if __name__ == "__main__":
    test_human_in_loop()
