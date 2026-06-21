.PHONY: install playground

install:
	uv sync

playground:
	agents-cli playground
