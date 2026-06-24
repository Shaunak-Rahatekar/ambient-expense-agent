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

The agent is deployed serverlessly to **Vertex AI Agent Runtime** (Reasoning Engine). Because the workflow involves pausing for Human-in-the-Loop, the best way to interact with the live cloud deployment is via the Google Cloud Console Playground.

1. **[Open the Cloud Console Playground](https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-east1/agent-engines/1395658487647698944/playground?project=ambient-expense-agent-500111)**
2. Submit an expense payload in JSON format:
   ```json
   {"amount": 5000, "description": "Client dinner", "date": "2026-06-04", "submitter": "Alice", "category": "Meals"}
   ```
3. The cloud agent will process the request and pause, waiting for human approval.
4. In the chat box, type `approve` (or `reject`) and hit enter to resume the workflow.

## Deployment & CI/CD

This project uses Terraform for infrastructure and GitHub Actions for CI/CD.
- The `deployment/terraform/single-project` directory contains the base infrastructure (Agent Engine, BigQuery Telemetry, Cloud Storage).
- The `.github/workflows` directory contains the CI/CD pipeline which automatically deploys the code in `app/` to the cloud upon merges to the `main` branch.

To deploy manually from the CLI:
```bash
agents-cli deploy
```

## Observability

The agent includes built-in telemetry that exports traces to Cloud Trace and logs to BigQuery (`ambient_expense_agent_telemetry` dataset) for custom analytics such as approval ratios.
