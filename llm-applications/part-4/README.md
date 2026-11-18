# Stream text and track completion

Use Go 1.24 or later. Display text deltas while tracking the response state.

## Run

```sh
go run .
```

Press Ctrl+C during a response to cancel. The app also applies a 30-second deadline.

The final state is complete, interrupted, or cancelled. Partial text can remain visible after failure.

The SSE parser supports multiline data, comments, and completion events. A DONE marker alone does not prove a completed answer.

Tests cover both documented text-event spellings, normal completion, truncated streams, malformed events, and cancellation.

Cancellation stops local waiting. It does not guarantee that provider-side work or billing is reversed.

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

```sh
go test ./...
go vet ./...
go build .
```

Unit tests use sample responses and make no live model calls. A configured key is required to check live model behavior.

`api.go` contains the HTTP helper. It checks HTTP status and response completion before the part reads the output.

The helper uses a fixed OpenRouter URL and hides error response bodies. Each request uses `store: false` and an output-token limit.

OpenRouter and provider retention policies can still apply. Instructions do not guarantee factual answers or enforce user access.
