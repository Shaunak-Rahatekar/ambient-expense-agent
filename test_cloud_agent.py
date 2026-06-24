import vertexai
from vertexai.preview import reasoning_engines

def test_human_in_loop():
    vertexai.init(project="ambient-expense-agent-500111", location="us-east1")
    agent_id = "projects/1042866970340/locations/us-east1/reasoningEngines/1395658487647698944"
    agent = reasoning_engines.ReasoningEngine(agent_id)

    session_id = "test-session-9999"
    payload = '{"amount": 5000, "description": "Client dinner", "date": "2026-06-04", "submitter": "Alice", "category": "Meals"}'

    print("=== Step 1: Submitting risky expense ===")
    response_iterator = agent.query(
        message=payload, 
        user_id="ambient-user", 
        session_id=session_id
    )
    
    events = response_iterator
    print(f"Response from Cloud:\n{events}\n")

    print("=== Step 2: Human Review ===")
    decision = input("Agent is paused. Type 'approve' or 'reject': ")

    print("\n=== Step 3: Resuming workflow ===")
    resume_iterator = agent.query(
        message=decision,
        user_id="ambient-user",
        session_id=session_id
    )
    
    final_events = resume_iterator
    print(f"\nFinal Response from Cloud:\n{final_events}\n")

if __name__ == "__main__":
    test_human_in_loop()
