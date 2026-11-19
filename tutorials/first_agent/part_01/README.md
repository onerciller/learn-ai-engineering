# Part 1: Give the Model One Tool

Describe one tool, see what goes wrong without checks, then run one checked search.

## Follow the code

1. Open `../tools.py`. `search_notes(query)` searches the sample JSON file. It does not call a model.
2. Read `SEARCH_NOTES_TOOL`. It tells the model the tool name, its purpose, and the required `query` string.
3. Read `run_unchecked` in `main.py`. It finds the `function_call`, decodes its JSON `arguments`, and runs whatever tool name the model chose.
4. Read `run`. `read_call` checks the tool name, call ID and JSON arguments. `search_query` checks the query. Only then does your code call `search_notes(query)`.
5. This part stops at the tool result. It does not ask the model to write a final answer yet.

## Run from the repository root

```sh
make run-python SERIES=first_agent PART=01
# Version 1, no checks:
make run-python SERIES=first_agent PART=01 ARGS='--unchecked'
# Break it: the simulated model asks for a tool that does not exist.
make run-python SERIES=first_agent PART=01 ARGS='--unchecked --demo-tool-name delete_notes'
make run-python SERIES=first_agent PART=01 ARGS='--demo-tool-name delete_notes'
# Run the search function alone, without even a simulated model:
make run-python SERIES=first_agent PART=01 ARGS='--demo-tool --query hiring'
```

The checked demo returns `reason: tool_result`, `steps: 1`, `tool_calls: 1`.
The match is **Launch plan**: “Finish onboarding. Risk: support scope is unclear.”
The unchecked app crashes with `KeyError('delete_notes')`; the checked app stops
with `Error: The requested tool is not allowed.`

The simulated model searches a word from your question. Try
`ARGS='--question "Find the hiring note"'`.

## Use a real model

```sh
make run-python SERIES=first_agent PART=01 ARGS='--live'
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

See the [series guide](../README.md#verification) for the full verification commands.

[All five parts](../README.md)
