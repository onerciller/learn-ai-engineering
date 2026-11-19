# Part 5: Connect Your Agent to MCP

Replace the local search function with a real call to the existing Go MCP server.

## Follow the code

1. Build `tutorials/mcp/part-1` into root `.bin/notes-server`.
2. Start that trusted executable over stdio using the official Python MCP SDK. Initialize the session.
3. Call `list_tools`, select only `search_notes`, and pass its actual description and input schema to the model.
4. Validate the requested tool, call ID and query, then validate the arguments against the discovered JSON Schema.
5. Call `session.call_tool`. Check the MCP error flag and decode the structured result or JSON text. This server returns plain strings; `search_result` turns each into `{"text": ...}`, the shape Parts 1–4 used.
6. Return the real result with the matching call ID, then continue until an answer or a stopping condition. SDK context managers close the session and child process.

## Run from the repository root

```sh
make build-mcp
make run-python SERIES=first_agent PART=05
make run-python SERIES=first_agent PART=05 ARGS='--query missing'
make integration-agent
```

The default demo returns `final_answer`, two model steps, one tool call, and:

> MCP tools offer actions with clearly defined input.

With `--query missing`, the first MCP search is empty. The result goes back to
the model, which searches `mcp` from the question and finds the same note.

These are the Go server's own sample notes, not `first_agent/data/notes.json`.
The model is simulated by default, but discovery, transport and search all use
the real Go process. No application-level draft tool is exposed in this part.
The server inherits the SDK's minimal default environment, not the whole shell
environment or your OpenRouter credentials.

Use `--server /absolute/path/to/trusted/server` only for a compatible executable
you trust. It receives no shell command or arguments. Default budgets are five
model steps, three tool calls and 60 seconds overall; MCP reads are capped at ten
seconds. Async timeout covers startup and transport. A model HTTP request already
running in a worker thread may take its own bounded timeout to finish on exit.

## Use a real model

```sh
make run-python SERIES=first_agent PART=05 ARGS='--live'
```

Configure the root `.env` as described in the [series guide](../README.md).
Use `--question 'your question'` to change the live request. `--query` only changes
the simulated model's first search word. Live requests may spend credits.
**Live model verification has not been run.** SDK behavior is tested with HTTP
fixtures; no successful live-model behavior is claimed.

## Check

```sh
uv run --locked pytest tests/first_agent
```

Build the Go binary first to include real MCP tests, or run `make integration-agent`.

[All five parts](../README.md)
