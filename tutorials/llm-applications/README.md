# How LLM applications work

Build a small notes app one step at a time with Go and OpenRouter.

| Part | Example |
| --- | --- |
| [Part 1](part-1/) | Send one question with a sample note and check the response. |
| [Part 2](part-2/) | Keep conversation history within an explicit text budget. |
| [Part 3](part-3/) | Request structured fields and check them in Go. |
| [Part 4](part-4/) | Stream text and track completion, interruption, and cancellation. |
| [Part 5](part-5/) | Connect one model tool call to the MCP notes server. |

All parts share the repository's root Go module. Run commands from the repository root; each part's README lists its command.

All parts use the root module’s Go 1.25.0 baseline and pinned MCP SDK.

The HTTP helper is repeated so each example runs independently. Live model calls require an OpenRouter key and available credits.

Local tests exercise deterministic behavior with fixtures. Part 5 also supports real MCP checks without model calls.
