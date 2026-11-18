# How LLM applications work

Build a small notes app one step at a time with Go and OpenRouter.

| Part | Example |
| --- | --- |
| [Part 1](part-1/) | Send one question with a sample note and check the response. |
| [Part 2](part-2/) | Keep conversation history within an explicit text budget. |
| [Part 3](part-3/) | Request structured fields and check them in Go. |
| [Part 4](part-4/) | Stream text and track completion, interruption, and cancellation. |
| [Part 5](part-5/) | Connect one model tool call to the MCP notes server. |

Each part is a separate Go module. Read the setup instructions in the part's folder.

Parts 1 through 4 use Go 1.24 or later. Part 5 needs Go 1.25 or later for its pinned MCP SDK.

The HTTP helper is repeated so each example runs independently. Live model calls require an OpenRouter key and available credits.

Local tests exercise deterministic behavior with fixtures. Part 5 also supports real MCP checks without model calls.
