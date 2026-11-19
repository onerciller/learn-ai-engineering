# One repository root, two languages

All lesson code is under `tutorials/`. Run commands from the repository root.
There is one Go module and one locked Python environment. No nested `go.mod`,
`go.work`, per-part `.venv`, or duplicate Python requirements files are needed.

## Existing lesson paths

| Old path | Current path |
| --- | --- |
| `mcp/part-1` through `mcp/part-5` | `tutorials/mcp/part-1` through `tutorials/mcp/part-5` |
| `llm-applications/part-1` through `part-5` | `tutorials/llm-applications/part-1` through `part-5` |

The Go source and test contents are preserved. Parts remain independent programs;
only their module boundary and repository paths changed. No dependency version
upgrade was required to combine the modules.

## Native commands

```sh
go mod download
go run ./tutorials/mcp/part-1
go test ./...
go vet ./...
go build ./...

uv sync --locked
uv run --locked python -m tutorials.first_agent
uv run --locked pytest
```

A future Python lesson uses `tutorials/<snake_case_series>/part_01/main.py` and
runs with `uv run --locked python -m tutorials.<series>.part_01.main`.
Go lessons preserve their existing `part-1` folder names.

## Make commands

```sh
make setup
make run-go SERIES=mcp PART=1
make run-go SERIES=llm-applications PART=2 ARGS='-chars 1200'
make build-mcp
make run-go SERIES=llm-applications PART=5 ARGS='-server ./.bin/notes-server -check-mcp -query tools'
make integration
make test
```

The LLM-to-MCP integration test runs the real Go MCP server and simulated model
responses; it does not contact a paid model. `make build-mcp` puts its executable
in the ignored root `.bin/` directory. Pass its path explicitly to Part 5.

GNU Make is optional; native Go and uv commands work directly, including on
Windows. Shell environment-variable examples use Bash/Zsh syntax; on PowerShell
set `$env:NOTES_SERVER_BIN` to the full server executable path before testing.

## Publishing path changes

GitHub source links in future articles must use
`https://github.com/onerciller/learn-ai-engineering/tree/main/tutorials/<series>/part-N`.
That main-branch URL becomes valid after this migration is committed and pushed.
The old root `mcp/` and `llm-applications/` compatibility folders have been
removed. Use only the `tutorials/` paths above; old root-folder links no longer
resolve on the main branch.
Existing scheduled article bodies and live publications are not modified by
moving this local repository.
