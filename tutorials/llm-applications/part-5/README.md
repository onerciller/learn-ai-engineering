# Connect the model to MCP search

Use Go 1.25 or later. This part pins the Go MCP SDK used by the original notes server.

## Build the server

From the tutorial repository root:

```sh
mkdir -p .bin
go build -o .bin/notes-server ./tutorials/mcp/part-1
```

The server binary must be trusted. The app starts it directly, with no inherited environment variables.

## Check MCP without a model

```sh
go run ./tutorials/llm-applications/part-5 -server ./.bin/notes-server -check-mcp -query tools
go run ./tutorials/llm-applications/part-5 -server ./.bin/notes-server -check-mcp -query zz-no-matching-note
```

The server searches its original three demo notes about MCP. These differ from the launch note used in earlier parts.

## Run the model request

Configure your API key and a model supporting function calls, then run:

```sh
go run ./tutorials/llm-applications/part-5 -server ./.bin/notes-server -question "Find the note about MCP tools."
```

The app obtains the search schema from MCP. It allows one search call, checks its arguments, and uses the matching call ID.

For matches, the app requests a final answer with further tools disabled. An empty result stops before the second model request.

The app preserves returned response items needed for continuation. It rejects a second tool call in the final response.

The server must enforce access to real user data. This example uses fixed public sample notes.

## Integration checks

From the repository root, set the compiled server's absolute path:

```sh
NOTES_SERVER_BIN="$PWD/.bin/notes-server" go test -tags=integration -count=1 -v ./tutorials/llm-applications/part-5
```

These checks use the real MCP server and simulated model responses. They verify schema transfer, result pairing, and the no-matches path.

They do not verify a live model's tool choice or answer quality.

## Requirements

- An OpenRouter API key with credits for live model requests.
- A model supporting this part's parameters.

Configure your account in Bash or Zsh:

```sh
export OPENROUTER_MODEL="anthropic/claude-haiku-4.5"
read -s OPENROUTER_API_KEY
export OPENROUTER_API_KEY
```

Press Enter after pasting the key. Keep it out of source files. Requests can incur charges.

Choose a model from the [OpenRouter catalog](https://openrouter.ai/models). Provider support for requested parameters can vary.

## Local checks

From the repository root:

```sh
mkdir -p .bin
go test ./tutorials/llm-applications/part-5
go vet ./tutorials/llm-applications/part-5
go build -o .bin/llm-part-5 ./tutorials/llm-applications/part-5
```

Unit tests use sample responses and make no live model calls. A configured key is required to check live model behavior.

`api.go` contains the HTTP helper. It checks HTTP status and response completion before the part reads the output.

The helper uses a fixed OpenRouter URL and hides error response bodies. Each request uses `store: false` and an output-token limit.

OpenRouter and provider retention policies can still apply. Instructions do not guarantee factual answers or enforce user access.
