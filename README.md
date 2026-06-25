# ambient-expense-agent

An intelligent, secure Expense Processing Agent built with the Google Agent Development Kit (ADK).

## What This Agent Does

The Ambient Expense Agent autonomously processes employee expense reports using a secure, multi-layered routing architecture:

1. **PII Scrubbing**: Automatically detects and redacts sensitive information (like SSNs and Credit Card numbers) from incoming requests before they reach the main LLM.
2. **Prompt Injection Detection**: Analyzes the input for malicious instructions or prompt injection attempts, isolating them for security review.
3. **Threshold Auto-Approval**: Evaluates the expense details. If the expense is clean, valid, and under the $100 threshold, it is automatically approved.
4. **Human-in-the-Loop (HITL) Review**: High-value expenses (>$100), policy violations, or suspicious requests are paused and routed to human review for explicit approval or rejection.

## Project Structure

```
ambient-expense-agent/
├── app/         # Core agent code and logic
├── tests/       # Unit, integration, and load tests
├── .github/     # GitHub Actions CI/CD workflows
├── deployment/  # Terraform infrastructure as code
└── pyproject.toml # Project dependencies
```

## How to Run Locally

To test the agent on your local machine with an interactive chat UI:

1. Install dependencies:
   ```bash
   uv tool install google-agents-cli
   uvx google-agents-cli setup
   agents-cli install
   ```

2. Start the local playground:
   ```bash
   agents-cli playground
   ```

3. Open the provided `localhost` URL in your browser. Try submitting a clean expense under $100, and then try submitting an expense over $100 to trigger the Human Review loop!

## How to Run on Cloud

The core agent is deployed serverlessly to **Vertex AI Agent Runtime** (Reasoning Engine), and we've deployed a custom **Cloud Run Dashboard** to handle the Human-in-the-Loop (HITL) review process!

### Option 1: Use the Custom Dashboard (Recommended for production)
1. **Submit an Expense:** You can submit an expense programmatically or use our local test script:
   ```bash
   uv run python test_cloud_agent.py
   ```
2. **Review Pending Expenses:** Navigate to the live **[Expense Manager Dashboard](https://expense-manager-dashboard-1042866970340.us-east1.run.app)**.
3. **Approve/Reject:** Any risky expense will automatically appear here. Click `Approve` or `Reject` to send the `FunctionResponse` payload back to the agent and resume the workflow!

### Option 2: Use the Vertex AI Playground (Recommended for debugging)
Because the workflow involves pausing for Human-in-the-Loop, you can also interact with the live cloud deployment directly via the Google Cloud Console Playground.
1. **[Open the Cloud Console Playground](https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-east1/agent-engines/2994999305317646336/playground?project=ambient-expense-agent-500111)**
2. Submit an expense payload in JSON format, or type it in plain text:
   ```json
   {"id": "EXP-101", "amount": 5000, "description": "Client dinner", "date": "2026-06-25", "submitter": "Alice", "employee_name": "Alice Smith", "merchant": "Steakhouse", "category": "Meals"}
   ```
3. The cloud agent will process the request and pause, asking for human approval.
4. In the chat box, type `approve` (or `reject`) and hit enter. The wrapper will automatically format this into the required `FunctionResponse` and resume the workflow.

## Deployment & CI/CD

This project uses Terraform for infrastructure and GitHub Actions for CI/CD.
- The `deployment/terraform/single-project` directory contains the base infrastructure (Agent Engine, BigQuery Telemetry, Cloud Storage).
- The `.github/workflows` directory contains the CI/CD pipeline which automatically deploys the code in `app/` to the cloud upon merges to the `main` branch.

To deploy manually from the CLI:
```bash
agents-cli deploy
```

The custom frontend is deployed via Cloud Run:
```bash
gcloud run deploy expense-manager-dashboard --source submission_frontend --region us-east1 --allow-unauthenticated --set-env-vars GOOGLE_CLOUD_PROJECT=ambient-expense-agent-500111,AGENT_RUNTIME_ID=projects/1042866970340/locations/us-east1/reasoningEngines/2994999305317646336
```

## Observability

The agent includes built-in telemetry that exports traces to Cloud Trace and logs to BigQuery (`ambient_expense_agent_telemetry` dataset) for custom analytics such as approval ratios.
