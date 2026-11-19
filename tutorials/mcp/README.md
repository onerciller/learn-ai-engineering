# Understanding MCP

Full code for the **Understanding MCP** series by [onerciller](https://onerciller.substack.com).

Each folder is the code for one part, and each one builds. Parts 1 and 2 are complete, working servers. In parts 3 to 5, things like data storage and email sending are simple placeholders in `placeholders.go`, so you can focus on the MCP parts.

| Folder | Part |
|---|---|
| `part-1` | Connect AI to Your Own Data: A Simple Intro to MCP |
| `part-2` | Tools, Resources, and Prompts in MCP: Who Decides? |
| `part-3` | When the AI Needs to Ask You: Confirmation, Progress, and Cancel in MCP |
| `part-4` | Who Gave Your AI Permission? MCP Security Basics |
| `part-5` | The Request Timed Out. Did Your AI Do It Twice? |

## Run it

You need Go 1.25+ and Node.js 22.19+.

From the repository root:

```bash
npx @modelcontextprotocol/inspector@2.13.0 --web --protocol-era modern go run ./tutorials/mcp/part-1
```

In Inspector, choose **Tools → search_notes** and send this input:

```json
{
  "query": "resource"
}
```

Expected result:

```json
{
  "matches": [
    "Resources give the assistant context."
  ]
}
```

Versions: MCP protocol revision 2026-07-28, Go SDK v1.8.0, Inspector 2.13.0.
