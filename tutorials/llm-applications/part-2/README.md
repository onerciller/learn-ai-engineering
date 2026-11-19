# Conversation history with a text budget

Use Go 1.25.0 or later. Keep recent user and assistant turns in process memory.

## Run

```sh
go run ./tutorials/llm-applications/part-2 -chars 1200
```

Ask about the launch task. Ask a follow-up about its day. Type `/quit` to stop.

The app drops whole old turns when their text exceeds the character budget. It preserves the rules, note, and current question.

This budget counts Unicode characters in content. It does not count model tokens or API framing, and cannot guarantee context-window fit.

The app reports actual token usage after completed requests. It saves a turn only after a completed text answer arrives.

Closing the process discards history. History removal also discards information.

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
go test ./tutorials/llm-applications/part-2
go vet ./tutorials/llm-applications/part-2
go build -o .bin/llm-part-2 ./tutorials/llm-applications/part-2
```

Unit tests use sample responses and make no live model calls. A configured key is required to check live model behavior.

`api.go` contains the HTTP helper. It checks HTTP status and response completion before the part reads the output.

The helper uses a fixed OpenRouter URL and hides error response bodies. Each request uses `store: false` and an output-token limit.

OpenRouter and provider retention policies can still apply. Instructions do not guarantee factual answers or enforce user access.
