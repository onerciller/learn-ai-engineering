"""Part 5: a Python agent calls the existing Go MCP notes server over stdio."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from jsonschema import Draft202012Validator
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from tutorials.first_agent.demo import DemoModel
from tutorials.first_agent.openrouter_client import (
    REPO_ROOT,
    OpenRouterClient,
    OpenRouterError,
)
from tutorials.first_agent.protocol import (
    AgentError,
    AgentResult,
    answer_text,
    continue_with_result,
    read_call,
    request,
    search_query,
    validate_limits,
)


def search_definition(tool) -> dict:
    if tool.name != "search_notes":
        raise AgentError("Only search_notes is allowed in this lesson.")
    Draft202012Validator.check_schema(tool.input_schema)
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description or "Search the MCP sample notes.",
        "parameters": tool.input_schema,
    }


def search_result(result) -> dict:
    if not isinstance(result, types.CallToolResult) or result.is_error:
        raise AgentError("MCP tool returned an error.")
    value = result.structured_content
    if value is None:
        texts = [c.text for c in result.content if isinstance(c, types.TextContent)]
        if len(texts) != 1:
            raise AgentError("Expected one MCP JSON result.")
        value = json.loads(texts[0])
    if not isinstance(value, dict) or not isinstance(value.get("matches"), list):
        raise AgentError("MCP result must contain a matches list.")
    if not all(isinstance(match, str) for match in value["matches"]):
        raise AgentError("Expected text matches from this Go server.")
    # The Go server returns plain strings. Give them the shape Parts 1–4 used.
    return {"matches": [{"text": match} for match in value["matches"]]}


def checked_message(error: BaseException) -> str:
    """Find our own check messages; never print raw server or provider data."""
    if isinstance(error, BaseExceptionGroup):
        return next(filter(None, map(checked_message, error.exceptions)), "")
    if isinstance(error, (AgentError, OpenRouterError)):
        return str(error)
    return ""


async def agent_loop(
    session, client, question, *, max_steps, max_tools, deadline, progress
):
    history = [{"role": "user", "content": question}]
    seen = set()
    tools = (await session.list_tools()).tools
    selected = [t for t in tools if t.name == "search_notes"]
    if len(selected) != 1:
        raise AgentError("The server must expose exactly one search_notes tool.")
    tool = search_definition(selected[0])
    for step in range(1, max_steps + 1):
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            return AgentResult(
                "deadline", "Stopped: time budget reached.", step - 1, len(seen)
            )
        progress["steps"] = step
        response = await asyncio.to_thread(
            client.create_response, request(history, [tool]), timeout_seconds=remaining
        )
        call = read_call(response, {"search_notes"}, seen)
        if call is None:
            return AgentResult("final_answer", answer_text(response), step, len(seen))
        query = search_query(call.arguments)
        Draft202012Validator(tool["parameters"]).validate(call.arguments)
        if len(seen) >= max_tools:
            return AgentResult(
                "tool_limit", "Stopped: tool-call limit reached.", step, len(seen)
            )
        result = search_result(
            await session.call_tool("search_notes", {"query": query})
        )
        seen.add(call.call_id)
        progress["tool_calls"] = len(seen)
        continue_with_result(history, response, call, result)
    return AgentResult(
        "step_limit", "Stopped: model step limit reached.", max_steps, len(seen)
    )


async def run(
    client,
    question: str,
    *,
    server: Path,
    max_steps=5,
    max_tools=3,
    timeout_seconds=60.0,
) -> AgentResult:
    validate_limits(question, max_steps, max_tools, timeout_seconds)
    server = server.resolve()
    if not server.is_file() or not os.access(server, os.X_OK):
        raise AgentError("Build the trusted server first: make build-mcp")
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    parameters = StdioServerParameters(command=str(server), args=[], env={})
    progress = {"steps": 0, "tool_calls": 0}
    try:
        # SDK context managers close the session and terminate the child process.
        async with asyncio.timeout(timeout_seconds):
            with open(os.devnull, "w") as server_log:
                async with stdio_client(parameters, errlog=server_log) as (
                    reader,
                    writer,
                ):
                    async with ClientSession(
                        reader, writer, read_timeout_seconds=min(10, timeout_seconds)
                    ) as session:
                        await session.initialize()
                        return await agent_loop(
                            session,
                            client,
                            question,
                            max_steps=max_steps,
                            max_tools=max_tools,
                            deadline=deadline,
                            progress=progress,
                        )
    except TimeoutError:
        return AgentResult(
            "deadline", "Stopped: MCP/model time budget reached.", **progress
        )
    except Exception as error:
        # Transport errors may contain server or provider data; show only ours.
        detail = checked_message(error)
        answer = "MCP or model request failed. The session was closed."
        return AgentResult("error", f"{answer} {detail}".strip(), **progress)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--server", type=Path, default=REPO_ROOT / ".bin/notes-server")
    parser.add_argument("--question", default="Find the note about MCP tools.")
    parser.add_argument("--query", help="Simulated model: first search word")
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--max-tools", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    try:
        client = OpenRouterClient.from_env() if args.live else DemoModel(args.query)
        result = asyncio.run(
            run(
                client,
                args.question,
                server=args.server,
                max_steps=args.max_steps,
                max_tools=args.max_tools,
                timeout_seconds=args.timeout,
            )
        )
        print(
            json.dumps(
                {
                    "mode": "live model + real Go MCP"
                    if args.live
                    else "simulated model + real Go MCP",
                    **result.as_dict(),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        if result.reason == "error":
            parser.exit(2)
    except (AgentError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
