# Tutorials

All Go and Python lesson code lives here. Go series use `part-1` names;
new Python series use `part_01` names.

- [Understanding MCP](mcp/): Go.
- [How LLM Applications Work](llm-applications/): Go.
- [Build Your First AI Agent](first_agent/): Python, five runnable parts with local tools, approval and a real Go MCP connection.

Go examples use the root module: `go run ./tutorials/mcp/part-1`.

New Python series go here. Each part runs independently from the repository root:

```sh
uv run --locked python -m tutorials.<series>.part_01.main
```

Use snake_case directory names, an `__init__.py` in each package, and
`part_01`, `part_02`, etc. Copy `templates/python-part/` when creating a part.
Do not create another environment, lockfile, or requirements file per part.
The first-agent series includes demo and live modes; demo models are simulated.

The first-agent OpenRouter SDK client lives under
`first_agent/openrouter_client.py` and loads the root `.env` only on request.
List the runnable lessons with `uv run --locked python -m tutorials.first_agent`.
There is no separate src package.
