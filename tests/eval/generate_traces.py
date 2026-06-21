import json
import asyncio
from typing import Dict, Any
from pathlib import Path
from app.expense_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def process_case(case: Dict[str, Any]) -> Dict[str, Any]:
    print(f"Processing case: {case['eval_case_id']}")
    prompt_text = case['prompt']['parts'][0]['text']
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="eval_app", user_id="eval_user", session_id=case['eval_case_id'])
    
    runner = Runner(agent=root_agent, app_name="eval_app", session_service=session_service)
    
    raw_events = []
    interrupt_id = None
    
    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])
    
    async for event in runner.run_async(user_id="eval_user", session_id=case['eval_case_id'], new_message=msg):
        raw_events.append(event)
        if type(event).__name__ == "RequestInput":
            interrupt_id = getattr(event, "interrupt_id", "human_approval")
            
    if interrupt_id:
        print(f"  HITL interrupted! Sending approval...")
        async for event in runner.run_async(
            user_id="eval_user", 
            session_id=case['eval_case_id'],
            resume_inputs={"human_approval": "approve"}
        ):
            raw_events.append(event)
            
    # Format events into strictly valid AgentEvents
    valid_events = []
    
    # 1. User turn
    valid_events.append({
        "author": "user",
        "content": msg.model_dump(mode='json')
    })
    
    # 2. Agent turns
    for event in raw_events:
        author = getattr(event, "author", "expense_agent")
        if author is None: author = "expense_agent"
        
        if getattr(event, "content", None) is not None:
            valid_events.append({
                "author": author,
                "content": getattr(event, "content").model_dump(mode='json')
            })
        elif getattr(event, "output", None) is not None:
            node_path = getattr(getattr(event, "node_info", None), "path", "unknown_node")
            valid_events.append({
                "author": author,
                "content": {
                    "role": "model",
                    "parts": [{"text": f"[{node_path} output]: {json.dumps(getattr(event, 'output'), default=str)}"}]
                }
            })
        elif type(event).__name__ == "RequestInput":
            valid_events.append({
                "author": author,
                "content": {
                    "role": "model",
                    "parts": [{"text": f"[HITL Interruption]: {getattr(event, 'message', '')}"}]
                }
            })
            
    return {
        "eval_case_id": case['eval_case_id'],
        "responses": [
            {
                "response": {
                    "role": "model",
                    "parts": [{"text": "Trace generated. See agent_data."}]
                }
            }
        ],
        "agent_data": {
            "agents": {
                "expense_agent": {
                    "agent_id": "expense_agent"
                }
            },
            "turns": [
                {
                    "turn_index": 0,
                    "events": valid_events
                }
            ]
        }
    }

async def main():
    dataset_path = Path("tests/eval/datasets/basic-dataset.json")
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
        
    output_cases = []
    for case in dataset.get("eval_cases", []):
        trace_case = await process_case(case)
        trace_case["prompt"] = case["prompt"]
        output_cases.append(trace_case)
        
    out_dir = Path("artifacts/traces")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "generated_traces.json"
    
    with open(out_file, "w") as f:
        json.dump({"eval_cases": output_cases}, f, indent=2)
        
    print(f"Traces written to {out_file}")

if __name__ == "__main__":
    asyncio.run(main())
