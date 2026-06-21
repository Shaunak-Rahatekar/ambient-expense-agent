.PHONY: install playground run
.PHONY: install playground run generate-traces grade

install:
	uv sync

playground:
	agents-cli playground

run:
	uv run python app/fast_api_app.py

.PHONY: generate-traces
generate-traces:
	uv run python tests/eval/generate_traces.py

.PHONY: grade
grade:
	uvx google-agents-cli eval grade --traces artifacts/traces/generated_traces.json --config tests/eval/eval_config.yaml
