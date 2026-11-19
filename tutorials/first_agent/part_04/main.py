"""Part 4: search notes, preview an email draft, and ask before saving it."""

import argparse
import json
import time
from pathlib import Path

from tutorials.first_agent.demo import DemoModel
from tutorials.first_agent.openrouter_client import (
    REPO_ROOT,
    OpenRouterClient,
    OpenRouterError,
)
from tutorials.first_agent.part_04.approval import (
    SAVE_DRAFT_TOOL,
    EmailDraft,
    ask_approval,
    save_approved_draft,
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
from tutorials.first_agent.tools import SEARCH_NOTES_TOOL, search_notes

DECLINED = {"approved": False, "saved": False, "email_sent": False}


def run(
    client,
    question: str,
    *,
    outbox: Path,
    max_steps=5,
    max_tools=3,
    timeout_seconds=60.0,
    approve=ask_approval,
    clock=time.monotonic,
) -> AgentResult:
    validate_limits(question, max_steps, max_tools, timeout_seconds)
    deadline = clock() + timeout_seconds
    history = [{"role": "user", "content": question}]
    seen, saved_drafts = set(), set()
    steps = 0

    def stop(reason: str, answer: str) -> AgentResult:
        return AgentResult(reason, answer, steps, len(seen))

    try:
        for step in range(1, max_steps + 1):
            remaining = deadline - clock()
            if remaining <= 0:
                return stop("deadline", "Stopped: time budget reached.")
            steps = step
            response = client.create_response(
                request(history, [SEARCH_NOTES_TOOL, SAVE_DRAFT_TOOL]),
                timeout_seconds=remaining,
            )
            if clock() >= deadline:
                return stop("deadline", "Stopped: time budget reached.")
            call = read_call(response, {"search_notes", "save_email_draft"}, seen)
            if call is None:
                return stop("final_answer", answer_text(response))
            if len(seen) >= max_tools:
                return stop("tool_limit", "Stopped: tool-call limit reached.")
            if clock() >= deadline:
                return stop("deadline", "Stopped: time budget reached.")
            if call.name == "search_notes":
                result = search_notes(search_query(call.arguments))
            else:
                draft = EmailDraft.from_arguments(call.arguments)
                preview = draft.preview()
                if preview in saved_drafts:
                    raise AgentError("The same draft was already saved in this run.")
                remaining = deadline - clock()
                if remaining <= 0:
                    return stop("deadline", "Stopped: time budget reached.")
                try:
                    approved = approve(preview, timeout_seconds=min(30.0, remaining))
                except TimeoutError:
                    return stop("deadline", "Approval timed out; no draft saved.")
                if clock() >= deadline:
                    return stop("deadline", "Approval arrived too late; not saved.")
                if not approved:
                    result = DECLINED  # Tell the model; it explains to the user.
                else:
                    # Save the same object the user saw, not a new model response.
                    result = save_approved_draft(draft, outbox)
                    saved_drafts.add(preview)
            seen.add(call.call_id)
            if clock() >= deadline:
                return stop("deadline", "Stopped: time budget reached.")
            continue_with_result(history, response, call, result)
    except (AgentError, OpenRouterError, ValueError, OSError) as error:
        if clock() >= deadline:
            return stop(
                "deadline",
                "Stopped: time budget reached. Check the outbox before retrying.",
            )
        return stop("error", f"Stopped: {error} Check the outbox before retrying.")
    return stop("step_limit", "Stopped: model step limit reached.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--question",
        default="Find the launch risk and save an email draft for "
        "learner@example.invalid. Do not send email.",
    )
    parser.add_argument("--query", help="Simulated model: first search word")
    parser.add_argument(
        "--outbox", type=Path, default=REPO_ROOT / ".local/first-agent/outbox.jsonl"
    )
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--max-tools", type=int, default=3)
    args = parser.parse_args()
    try:
        client = (
            OpenRouterClient.from_env()
            if args.live
            else DemoModel(args.query, email=True)
        )
        result = run(
            client,
            args.question,
            outbox=args.outbox,
            timeout_seconds=args.timeout,
            max_steps=args.max_steps,
            max_tools=args.max_tools,
        )
        mode = (
            "live model; simulated local outbox"
            if args.live
            else "simulated model; real local tools"
        )
        print(
            json.dumps({"mode": mode, **result.as_dict()}, indent=2, ensure_ascii=False)
        )
        if result.reason == "error":
            parser.exit(2)
    except (AgentError, OpenRouterError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
