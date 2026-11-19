# Shared Python tutorial environment

All new Python lessons share one environment at the repository root. Existing Go
examples in `tutorials/mcp/` and `tutorials/llm-applications/` share the root
`go.mod` and `go.sum`.

## Fixed baseline

- Python: **3.12.11**, matching `.python-version` and `project.requires-python`.
- uv: **0.7.12**, enforced by `tool.uv.required-version` in `pyproject.toml`.
- Direct dependencies use exact `==` constraints in `pyproject.toml`.
- Transitive dependencies and package hashes are recorded in **uv.lock**.
- This repository is not an installable Python package; uv manages dependencies
  only (`package = false`). Modules run directly from the repository root.
- CI actions are pinned to commit IDs. CI installs the project's pinned Python
  and uv versions on Linux, macOS and Windows.

These are the chosen baseline versions, not a claim that they are the latest.
Changing them is an explicit maintenance task, not part of installing a lesson.

## Install once

Install the exact uv version using the official versioned installer:

macOS / Linux:

```sh
curl -LsSf https://astral.sh/uv/0.7.12/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.7.12/install.ps1 | iex"
```

Open a new terminal, then from the repository root:

```sh
uv --version
uv python install
uv sync --locked
uv run --locked python -m tutorials.first_agent
```

The last command lists the runnable first-agent lessons offline. It does not need credentials,
call a model, or spend credits. `uv` manages `.venv`; no activation is required.
A mismatched uv version is rejected rather than silently resolving a different
lockfile. Use the installer above to obtain the required version.

## Repository layout

```text
.python-version
pyproject.toml
uv.lock
.env.example
tutorials/
    first_agent/
        __main__.py           # Offline lesson list: python -m tutorials.first_agent
        tools.py              # Real local search and tool schema
        protocol.py           # Tool-call validation and history helpers
        demo.py               # Explicitly simulated model
        openrouter_client.py  # Official OpenRouter SDK; root .env loading
        part_01/ ... part_05/ # Runnable Python agent lessons
    mcp/                      # Existing Go lessons
    llm-applications/         # Existing Go lessons
    <python_series>/          # Added as lessons are written
        __init__.py
        part_01/
            __init__.py
            main.py
            tools.py          # Only if needed
            README.md
tests/
    test_config.py
    <series>/test_part_01.py
templates/python-part/        # Starter files, not a finished tutorial
.github/workflows/python.yml
```

All commands run from the repository root. Copy the starter folder for each new
part and add `__init__.py` to the series directory. The runnable command is:

```sh
uv run --locked python -m tutorials.<series>.part_01.main
```

Replace `<series>` with the real module name. A part must not depend on running a
previous part first. Keep prompts, small sample data, and lesson-specific logic
beside its `main.py`; keep reusable configuration in `tutorials/`.

## Model configuration

Copy `.env.example` to `.env` once when a lesson first needs a model. Set:

```dotenv
OPENROUTER_API_KEY=your-local-key
OPENROUTER_MODEL=the-exact-model-id-recorded-in-the-lesson
```

The first-agent client uses the official `openrouter==1.3.194` SDK and its
Responses endpoint at `https://openrouter.ai/api/v1/responses`. Automatic retries
are disabled. Tool execution and the agent loop remain in each part's `main.py`.
Configuration is loaded on request, not at import time; shell values take
precedence. No default model is selected silently. Use `--live` explicitly;
default agent commands simulate the model and use real tools.

The shared environment also pins `mcp==2.3.0` for the Python-to-Go stdio connection,
`jsonschema==4.26.0` for discovered tool schemas, `httpx==0.28.1` for transport,
and `python-dotenv==1.2.4` for root environment loading. These are exact direct
constraints, with transitive versions and hashes in `uv.lock`.

Record the tested model ID in the lesson README. A package lockfile fixes local
software versions; it cannot guarantee remote model availability or identical
model output. Tests use local fixtures/mocks; real model checks are separate and
must be reported as real or not run.

## Daily checks

```sh
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

## Controlled dependency changes

Do not edit uv.lock by hand or create a second requirements file. When a lesson
needs a new package, select an exact version, then update the shared environment:

```sh
uv add package-name==X.Y.Z
uv sync --locked
```

Run all existing Python tests and affected lesson commands before accepting the
change. Record version changes in the associated commit/PR. For Python updates,
change both version pins together; for uv updates, change `required-version` and
the versioned installation instructions together. Refresh the lock deliberately.

References: [uv project locking](https://docs.astral.sh/uv/concepts/projects/sync/),
[uv required-version](https://docs.astral.sh/uv/reference/settings/#required-version),
[OpenRouter API](https://openrouter.ai/docs/quickstart).
