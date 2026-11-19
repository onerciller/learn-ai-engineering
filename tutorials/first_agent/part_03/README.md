# Part 3: Know When to Stop

Give the loop a model-step budget, a tool-call budget and a time budget.

## Follow the code

1. Run the stubborn model first. It never stops asking for searches, so something must stop it.
2. Validate the question and limits before starting: 1–20 model steps, 0–20 tool calls, and a finite positive timeout.
3. Limit 1: before each model request, calculate the remaining time and pass it to the SDK wrapper.
4. Limit 2: check the tool budget before running a tool.
5. Limit 3: check the deadline immediately after the model response. Reject late answers and tool requests. Recheck before and after tool execution.
6. Read `reason` in the returned JSON. On `error`, `answer` carries the failed check's message. Never retry a failed request automatically.

## Run from the repository root

```sh
make run-python SERIES=first_agent PART=03
make run-python SERIES=first_agent PART=03 ARGS='--stubborn-model'
make run-python SERIES=first_agent PART=03 ARGS='--stubborn-model --max-tools 10'
make run-python SERIES=first_agent PART=03 ARGS='--max-tools 0'
make run-python SERIES=first_agent PART=03 ARGS='--timeout 0.000001'
```

Default limits: five model steps, three tool calls, 60 seconds overall. The first
example returns `final_answer`. The stubborn model hits `tool_limit` after four
steps and three tool calls; with ten tool calls allowed, it hits `step_limit`
after five steps. `--max-tools 0` returns `tool_limit` before any search, and
the tiny timeout returns `deadline`.

## Use a real model

```sh
make run-python SERIES=first_agent PART=03 ARGS='--live'
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
