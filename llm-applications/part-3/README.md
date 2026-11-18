# Structured note summaries

Use Go 1.24 or later. Request title and summary fields through the OpenRouter Responses API.

## Run

```sh
go run .
```

Choose an endpoint supporting structured output. Requests use `text.format` with a JSON schema and `provider.require_parameters: true`.

Strict handling varies by provider. The app also rejects missing values, unknown fields, invalid types, and trailing JSON.

The local parser checks shape and non-empty text. It does not prove the summary's facts match the note.

Tests include a well-shaped but invented summary to show that limit.

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
