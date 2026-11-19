"""Part 1: model request -> checked tool call -> local tool result."""

import argparse
import json

from tutorials.first_agent.demo import DemoModel
from tutorials.first_agent.openrouter_client import OpenRouterClient, OpenRouterError
from tutorials.first_agent.protocol import (
    AgentError,
    AgentResult,
    answer_text,
    read_call,
    request,
    search_query,
)
from tutorials.first_agent.tools import SEARCH_NOTES_TOOL, search_notes

TOOLS = {"search_notes": search_notes}


def run_unchecked(client, question: str) -> dict:
    """Version 1 trusts the model completely. Read it, then never ship it."""
    history = [{"role": "user", "content": question}]
    response = client.create_response(request(history, [SEARCH_NOTES_TOOL]))
    call = next(i for i in response["output"] if i["type"] == "function_call")
    arguments = json.loads(call["arguments"])  # Arguments arrive as JSON text.
    tool = TOOLS[call["name"]]  # Whatever name the model chose...
    return tool(**arguments)  # ...runs with whatever input it chose.


def run(client, question: str) -> AgentResult:
    if not question.strip():
        raise AgentError("Question must not be empty.")
    history = [{"role": "user", "content": question}]
    payload = request(history, [SEARCH_NOTES_TOOL], force_search=True)
    response = client.create_response(payload)
    call = read_call(response, {"search_notes"})
    if call is None:
        return AgentResult("final_answer", answer_text(response), 1, 0)
    query = search_query(call.arguments)
    result = search_notes(query)
    return AgentResult("tool_result", json.dumps(result, ensure_ascii=False), 1, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Call OpenRouter; may spend credits"
    )
    parser.add_argument(
        "--demo-tool", action="store_true", help="Run local search only"
    )
    parser.add_argument(
        "--unchecked", action="store_true", help="Run version 1 with no checks"
    )
    parser.add_argument("--question", default="Find the launch note.")
    parser.add_argument("--query", help="Simulated model: search this word instead")
    parser.add_argument(
        "--demo-tool-name",
        default="search_notes",
        help="Simulated model: ask for this tool name",
    )
    args = parser.parse_args()
    try:
        if args.demo_tool:
            print(
                json.dumps(
                    search_notes(args.query or "launch"), indent=2, ensure_ascii=False
                )
            )
            return

        client = (
            OpenRouterClient.from_env()
            if args.live
            else DemoModel(args.query, tool_name=args.demo_tool_name)
        )
        if args.unchecked:
            try:
                print(
                    json.dumps(
                        run_unchecked(client, args.question),
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            except Exception as error:  # Show exactly how the unchecked app breaks.
                parser.exit(2, f"Unchecked app crashed: {error!r}\n")
            return
        result = run(client, args.question)
        mode = "live" if args.live else "simulated model + real local tool"
        print(
            json.dumps({"mode": mode, **result.as_dict()}, indent=2, ensure_ascii=False)
        )
    except (AgentError, OpenRouterError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
