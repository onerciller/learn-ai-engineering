# Your first model request

Ask a question about a sample note with the OpenRouter Responses API. This example uses only the Go standard library.

## Requirements

- Go 1.25.0 or later.
- An OpenRouter API key with model access and available credits.
- A model that supports the Responses API.

## Run

From the repository root, configure your model:

```sh
export OPENROUTER_MODEL="anthropic/claude-haiku-4.5"
read -s OPENROUTER_API_KEY
export OPENROUTER_API_KEY
go run ./tutorials/llm-applications/part-1
```

The hidden key prompt works in Bash and Zsh. Press Enter after pasting your key. API requests can incur charges.

Ask another question:

```sh
go run ./tutorials/llm-applications/part-1 -question "Who owns the launch?"
```

The sample note contains no owner. Check whether the response admits that missing information.

Requests go to `https://openrouter.ai/api/v1/responses`. OpenRouter routes each request to a model provider.

Use a model identifier from the [OpenRouter catalog](https://openrouter.ai/models). Access depends on your account and provider availability.

## Behavior

The app sends instructions, one fixed sample note, and your question. It makes one request with a 30-second deadline.

The app rejects HTTP errors, incomplete responses, and responses without text. Error bodies are not printed.

Completed text can still be inaccurate. Compare the answer with the note. The instructions are not a security boundary.

The request uses `store: false`. OpenRouter and provider data policies can still apply. Cancellation does not guarantee a charge is avoided.

## Check the code

From the repository root:

```sh
mkdir -p .bin
go test ./tutorials/llm-applications/part-1
go vet ./tutorials/llm-applications/part-1
go build -o .bin/llm-part-1 ./tutorials/llm-applications/part-1
```

Tests cover empty input, error-body redaction, cancellation, incomplete output, refusal, and text following a non-message item. Tests make no external requests.

## API contract

The example reads `output` message items and their `output_text` content. It also reads completion status and token usage.

See the [Responses API reference](https://openrouter.ai/docs/api_reference/responses/basic-usage) for the request and response contract.
