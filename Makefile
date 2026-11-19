.DEFAULT_GOAL := help
SERIES ?= mcp
PART ?= 1
ARGS ?=

.PHONY: help setup test test-go test-python integration run-go run-python build-mcp integration-agent demo-agent

help:
	@echo "make setup                       Install the locked Python environment and Go dependencies"
	@echo "make run-go SERIES=mcp PART=1     Run a Go lesson (extra flags: ARGS='...')"
	@echo "make run-python SERIES=... PART=01  Run a Python lesson"
	@echo "make demo-agent                  Run the first-agent read-only demos"
	@echo "make integration-agent           Test the Python agent with the real Go MCP server"
	@echo "make test                        Check all Go and Python code"
	@echo "make integration                 Test the real Go MCP server with simulated model responses"

setup:
	go mod download
	uv sync --locked

run-go:
	go run ./tutorials/$(SERIES)/part-$(PART) $(ARGS)

run-python:
	uv run --locked python -m tutorials.$(SERIES).part_$(PART).main $(ARGS)

test: test-go test-python

test-go:
	go mod verify
	go test ./...
	go vet ./...
	go build ./...

test-python:
	uv sync --locked
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked pytest

build-mcp:
	mkdir -p .bin
	go build -o .bin/notes-server ./tutorials/mcp/part-1

integration: build-mcp
	NOTES_SERVER_BIN="$(CURDIR)/.bin/notes-server" go test -tags=integration -count=1 -v ./tutorials/llm-applications/part-5

# Real Go MCP server + simulated model. No OpenRouter credits required.
integration-agent: build-mcp
	NOTES_SERVER_BIN="$(CURDIR)/.bin/notes-server" uv run --locked pytest tests/first_agent/test_mcp.py

# All read-only demos; Part 4 approval is intentionally left interactive.
demo-agent: build-mcp
	uv run --locked python -m tutorials.first_agent.part_01.main
	uv run --locked python -m tutorials.first_agent.part_02.main
	uv run --locked python -m tutorials.first_agent.part_03.main
	uv run --locked python -m tutorials.first_agent.part_05.main
