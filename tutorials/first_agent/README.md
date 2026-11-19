# Build Your First AI Agent

Five runnable Python lessons. Start with one checked tool call and finish with a
Python agent that searches notes through the existing Go MCP server.

The model requests an action. Your application checks it and runs the tool.
Each lesson keeps that flow visible in its own `main.py`.

## The five parts

| Part | Lesson | What runs |
| --- | --- | --- |
| [01](part_01/) | Give the Model One Tool | Describe `search_notes`, validate one request, run the search |
| [02](part_02/) | Let the Agent Take Another Step | Return the tool result with its call ID and continue until an answer |
| [03](part_03/) | Know When to Stop | Limit model steps, tool calls and elapsed time; handle errors |
| [04](part_04/) | Ask Before Acting | Preview an email draft and save it locally only after approval |
| [05](part_05/) | Connect Your Agent to MCP | Discover and call `search_notes` on the real Go MCP server |

## Run from the repository root

Python **3.12.11**, uv **0.7.12**. See [environment setup](../../docs/python-setup.md).
Part 5 also uses the root Go toolchain and dependencies.

```sh
uv sync --locked
uv run --locked python -m tutorials.first_agent

# Build the MCP server and run the four read-only demos:
make demo-agent

# Part 4 is interactive. Type yes to save the displayed draft, or no to decline:
make run-python SERIES=first_agent PART=04
```

The default model is a deterministic simulation from `demo.py`. It reads your
`--question` and searches a word from it, so changing the question changes the
run. The local tools and the Part 5 MCP connection are real. No API key or model
credits are needed. `--query` overrides only the simulated model's first search.

Examples to explore:

```sh
make run-python SERIES=first_agent PART=01 ARGS='--unchecked --demo-tool-name delete_notes'
make run-python SERIES=first_agent PART=02 ARGS='--query missing --trace'
make run-python SERIES=first_agent PART=03 ARGS='--stubborn-model'
make run-python SERIES=first_agent PART=03 ARGS='--max-tools 0'
```

The first crashes the unchecked version on purpose. The second searches twice:
the empty result goes back to the model, which tries `launch`. `--trace` prints
the history the model reads on every step. The last two return `tool_limit`.

## Use OpenRouter

Copy the root `.env.example` to `.env` if you do not already have one. Set your
API key and an **explicit model ID** that supports tool calling through the
Responses API. No model is chosen by default.

```dotenv
OPENROUTER_API_KEY=your-local-key
OPENROUTER_MODEL=your-explicit-model-id
```

```sh
make run-python SERIES=first_agent PART=02 ARGS='--live'
# Part 5 still needs make build-mcp first:
make run-python SERIES=first_agent PART=05 ARGS='--live'
```

The official `openrouter==1.3.194` SDK sends one non-streaming Responses request
per step. Automatic retries are disabled; each HTTP call has a maximum 30-second
timeout. Shell environment variables override root `.env` values. Credentials
are loaded only for `--live` and are not printed.

**Live verification: not run.** No real model ID or successful live response is
claimed. Tests exercise the actual SDK using an intercepted HTTP transport;
agent decisions use explicit fixtures. Record the exact model ID and date here
after a live check. A lockfile fixes local packages, not remote model behavior.

## Files to read

```text
first_agent/
    data/notes.json               Local sample notes for Parts 1–4
    tools.py                      Search function and its tool definition
    protocol.py                   Argument checks, limits, call IDs, history and --trace
    demo.py                       Simulated model that reads the question and history
    openrouter_client.py          Shared official OpenRouter SDK wrapper
    part_01/main.py               Unchecked, then checked, single tool call
    part_02/main.py               15-line loop, then the checked loop
    part_03/main.py               Budgets and stop reasons
    part_04/main.py               Approval before saving a local draft
    part_04/approval.py           Immutable preview and local outbox
    part_05/main.py               Real MCP session and agent loop
```

Parts 1–4 search `data/notes.json`. Part 5 searches the **Go server's own sample
notes** in `tutorials/mcp/part-1/main.go`; these are different datasets. Part 5
turns the server's plain-string matches into `{"text": ...}` objects, the same
shape Parts 1–4 use. Each part
starts independently and does not require files from an earlier part's run.

## Results and limits

The JSON result includes `reason`, `answer`, `steps` (model requests attempted)
and `tool_calls` (successful tool calls). Part 1 stops at the tool result; later
parts can produce a final answer. An empty search is returned to the model like
any other result; the model decides whether to try another word or say nothing
matched. Invalid input, provider failures and invalid tool requests exit the CLI
with code 2; from Part 3 on they return `reason: error` with the check's message.
Use `reason`, not exit code alone, to distinguish a final answer from a limit.

Only allowlisted tools run, one call per model turn. Arguments and call IDs are
checked before execution. Part 3 introduces independent step, tool and elapsed
time budgets. Local file operations are checked between steps, not forcibly
interrupted. A model-call timeout can return an error before the overall budget
is exhausted. These teaching limits do not make model-generated text trustworthy.

Part 4 saves **simulated email drafts**, never sends email. Only an explicit
`yes` accepts the displayed immutable payload. Any other answer, or closed input,
writes nothing; the model receives `{"approved": false}` and explains it while time remains.
Approval waits at most 30 seconds or the remaining overall budget. A timeout
stops with `deadline` without saving or making another model request. Late
answers and tool requests also stop before new work. Approved drafts append to
root `.local/first-agent/outbox.jsonl`
(ignored by Git). Duplicate prevention is per run; rerunning and approving again
can append another draft. If a write fails, inspect the outbox before retrying.

Part 5 runs only the selected trusted executable without a shell. The official
`mcp==2.3.0` SDK discovers the tool schema, validates arguments, pairs results and
closes the server process. It exposes search only, so no write approval is needed.
The overall async deadline covers startup and MCP operations; an in-flight SDK
HTTP call in a worker thread may finish at its own bounded timeout during exit.

## Verification

```sh
make test-python
make integration-agent
make demo-agent
```

Verified on 2026-11-19 (macOS, Python 3.12.11, uv 0.7.12): **86 Python tests
passed**, including six real MCP integration tests and eleven deadline regression
checks. Ruff lint and formatting passed. The Part 4 CLI exited after its approval
wait expired without creating an outbox file.

Tests cover actual local searches, SDK request serialization and errors, multi-turn
history, retries after empty results, missing call results, malformed requests,
repeated call IDs, stopping limits, approval rejection, exact preview/save matching, and the real Go MCP server. Ordinary
pytest skips server-dependent tests if the binary has not been built;
`make integration-agent` builds it and requires those tests to run. CI includes a
separate real MCP integration job. No test needs a paid model call.
