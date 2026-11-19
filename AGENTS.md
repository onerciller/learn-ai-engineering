# Learn AI Engineering code conventions

- All lesson code lives under tutorials/: existing Go series are tutorials/mcp
  and tutorials/llm-applications. New series use Python.
- Go uses the single root go.mod/go.sum. Do not add nested modules or go.work.
- Run Go examples from the repository root: go run ./tutorials/<series>/part-N.
- Use the golang-how-to skill for Go work.
- New tutorials use Python. Python agents may connect to the existing Go MCP server.
- Read docs/python-setup.md before adding a Python tutorial or dependency.
- One root pyproject.toml, uv.lock, .python-version and .venv for all Python lessons.
- Use the exact uv required-version in pyproject.toml. Never upgrade implicitly.
- Use `uv sync --locked` and `uv run --locked`; no per-part requirements files,
  independent virtual environments, inline script dependencies, or pip installs.
- New lessons: tutorials/<snake_case_series>/part_01/main.py, part_02, etc.
  Each part runs independently from the repository root via `python -m ...`.
- Starter files are in templates/python-part; placeholders must be replaced before
  a lesson is listed as completed in README.md.
- Configuration and model client code belong under tutorials/, never under src/.
  Lesson-specific tool and agent logic belongs with the lesson; avoid hiding teaching logic in shared helpers.
- Model provider is OpenRouter. Use root .env.example variable names, root config
  loading and the series’ official OpenRouter SDK client. Never commit .env or real API credentials.
- Record the exact model ID used for each lesson. Do not silently choose a model
  or use latest/automatic aliases in reproducibility examples.
- Dependency updates are deliberate: change the exact constraint, refresh uv.lock,
  run all Python tests and existing lesson smoke checks, and document the change.
- Before delivery: `uv sync --locked`, `uv run --locked python -m tutorials.first_agent`,
  `uv run --locked ruff check .`, `uv run --locked ruff format --check .`,
  `uv run --locked pytest`. API calls are separate from offline checks.
