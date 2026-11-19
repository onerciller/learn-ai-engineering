"""Part 3: explicit step, tool-call and overall time budgets."""

import argparse
import json
import time

from tutorials.first_agent.demo import DemoModel
from tutorials.first_agent.openrouter_client import OpenRouterClient, OpenRouterError
from tutorials.first_agent.protocol import (
    AgentError,
    AgentResult,
    answer_text,
    continue_with_result,
    read_call,
    request,
    search_query,
    show_history,
    validate_limits,
)
from tutorials.first_agent.tools import SEARCH_NOTES_TOOL, search_notes


def run(
    client,
    question: str,
    *,
    max_steps=5,
    max_tools=3,
    timeout_seconds=60.0,
    clock=time.monotonic,
    search=search_notes,
    trace=None,
) -> AgentResult:
    validate_limits(question, max_steps, max_tools, timeout_seconds)
    deadline = clock() + timeout_seconds
    history = [{"role": "user", "content": question}]
    seen = set()
    steps = 0

    def stop(reason: str, answer: str) -> AgentResult:
        return AgentResult(reason, answer, steps, len(seen))

    try:
        for step in range(1, max_steps + 1):
            if trace:
                trace(step, history)
            remaining = deadline - clock()
            if remaining <= 0:  # Limit 1: is there time to ask the model?
                return stop("deadline", "Stopped: time budget reached.")
            steps = step
            response = client.create_response(
                request(history, [SEARCH_NOTES_TOOL]), timeout_seconds=remaining
            )
            if clock() >= deadline:  # Limit 3: reject any response that arrives late.
                return stop("deadline", "Stopped: time budget reached.")
            call = read_call(response, {"search_notes"}, seen)
            if call is None:
                return stop("final_answer", answer_text(response))
            query = search_query(call.arguments)
            if len(seen) >= max_tools:  # Limit 2: is a tool call left?
                return stop("tool_limit", "Stopped: tool-call limit reached.")
            if clock() >= deadline:  # Recheck before starting the tool.
                return stop("deadline", "Stopped: time budget reached.")
            result = search(query)
            seen.add(call.call_id)
            if clock() >= deadline:
                return stop("deadline", "Stopped: time budget reached.")
            continue_with_result(history, response, call, result)
    except (AgentError, OpenRouterError, ValueError, OSError) as error:
        if clock() >= deadline:
            return stop("deadline", "Stopped: time budget reached.")
        return stop("error", f"Stopped: {error}")
    return stop("step_limit", "Stopped: model step limit reached.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--question", default="Find the launch note and tell me its risk."
    )
    parser.add_argument("--query", help="Simulated model: first search word")
    parser.add_argument(
        "--stubborn-model",
        action="store_true",
        help="Simulated model that never stops asking for searches",
    )
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--max-tools", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    try:
        client = (
            OpenRouterClient.from_env()
            if args.live
            else DemoModel(args.query, stubborn=args.stubborn_model)
        )
        result = run(
            client,
            args.question,
            max_steps=args.max_steps,
            max_tools=args.max_tools,
            timeout_seconds=args.timeout,
            trace=show_history if args.trace else None,
        )
        mode = "live" if args.live else "simulated model + real local tool"
        print(
            json.dumps({"mode": mode, **result.as_dict()}, indent=2, ensure_ascii=False)
        )
        if result.reason == "error":
            parser.exit(2)
    except (AgentError, OpenRouterError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
