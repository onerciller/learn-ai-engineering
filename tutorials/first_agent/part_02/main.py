"""Part 2: return tool results to the model and continue a bounded loop."""

import argparse
import json

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
)
from tutorials.first_agent.tools import SEARCH_NOTES_TOOL, search_notes


def run_minimal(client, question, max_steps=5):
    history = [{"role": "user", "content": question}]
    for step in range(1, max_steps + 1):
        response = client.create_response(request(history, [SEARCH_NOTES_TOOL]))
        calls = [i for i in response["output"] if i["type"] == "function_call"]
        if not calls:  # 1. No tool request: this is the answer.
            return answer_text(response)
        call = calls[0]
        args = json.loads(call["arguments"])  # 2. Arguments arrive as JSON text.
        result = search_notes(args["query"])  # 3. YOUR code runs the tool.
        history += response["output"]  # 4. Remember what the model asked...
        history.append(  # 5. ...and what the tool returned.
            {
                "type": "function_call_output",
                "call_id": call["call_id"],
                "output": json.dumps(result),
            }
        )
    return "Stopped: step limit reached."


def run(client, question: str, *, max_steps: int = 5, trace=None) -> AgentResult:
    if not question.strip() or not 1 <= max_steps <= 20:
        raise AgentError("Provide a question and 1–20 model steps.")
    history = [{"role": "user", "content": question}]
    seen = set()
    for step in range(1, max_steps + 1):
        if trace:
            trace(step, history)
        response = client.create_response(request(history, [SEARCH_NOTES_TOOL]))
        call = read_call(response, {"search_notes"}, seen)
        if call is None:
            return AgentResult("final_answer", answer_text(response), step, len(seen))
        result = search_notes(search_query(call.arguments))
        seen.add(call.call_id)
        # An empty result goes back too. The model decides what to do next.
        continue_with_result(history, response, call, result)
    return AgentResult(
        "step_limit", "Stopped: model step limit reached.", max_steps, len(seen)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--question", default="Find the launch note and tell me its risk."
    )
    parser.add_argument("--query", help="Simulated model: first search word")
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument(
        "--trace", action="store_true", help="Print the history before each step"
    )
    parser.add_argument(
        "--minimal", action="store_true", help="Run the 15-line loop with no checks"
    )
    args = parser.parse_args()
    try:
        client = OpenRouterClient.from_env() if args.live else DemoModel(args.query)
        if args.minimal:
            print(run_minimal(client, args.question, args.max_steps))
            return
        trace = show_history if args.trace else None
        result = run(client, args.question, max_steps=args.max_steps, trace=trace)
        mode = "live" if args.live else "simulated model + real local tool"
        print(
            json.dumps({"mode": mode, **result.as_dict()}, indent=2, ensure_ascii=False)
        )
    except (AgentError, OpenRouterError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
