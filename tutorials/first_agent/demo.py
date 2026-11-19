"""A scripted stand-in for a real model. The tools it asks for run for real.

DemoModel reads the question and the tool results in the history, as a model
would. Its choices follow fixed rules, so every run gives the same output.
"""

import json
import re

from tutorials.first_agent.protocol import AgentError

# Words the simulated model knows how to search for, in the order it prefers.
KNOWN_WORDS = ("launch", "hiring", "support", "mcp", "tools", "permission")
FILLER = {"find", "note", "notes", "the", "and", "tell", "about", "its", "save"}


def tool_call(call_id: str, name: str, arguments: dict) -> dict:
    return {
        "status": "completed",
        "output": [
            {
                "type": "function_call",
                "call_id": call_id,
                "name": name,
                "arguments": json.dumps(arguments),
            }
        ],
    }


def message(text: str) -> dict:
    return {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            }
        ],
    }


def check_pairs(history: list) -> None:
    """Reject a request the way a real API does: every call needs its result."""
    calls = [i["call_id"] for i in history if i.get("type") == "function_call"]
    outputs = {
        i.get("call_id") for i in history if i.get("type") == "function_call_output"
    }
    for call_id in calls:
        if call_id not in outputs:
            raise AgentError(
                f"Request rejected: function_call {call_id!r} has no "
                "function_call_output with the same call_id."
            )


def words_in(question: str) -> list[str]:
    words = re.findall(r"[a-z]+", question.casefold())
    return [word for word in words if word in KNOWN_WORDS]


def first_word(question: str) -> str:
    """Prefer a known word; otherwise search the first meaningful word."""
    if words_in(question):
        return words_in(question)[0]
    words = re.findall(r"[a-z]+", question.casefold())
    return next((w for w in words if len(w) > 2 and w not in FILLER), "notes")


class DemoModel:
    def __init__(
        self,
        query: str | None = None,
        *,
        email: bool = False,
        tool_name: str = "search_notes",
        stubborn: bool = False,
    ):
        self.query = query  # Overrides the first search word, for experiments.
        self.email = email  # Part 4: offer to save an email draft.
        self.tool_name = tool_name  # Part 1: ask for a tool that may not exist.
        self.stubborn = stubborn  # Part 3: never stop asking for searches.
        self.calls = 0

    def create_response(self, payload: dict, *, timeout_seconds: float = 30) -> dict:
        self.calls += 1
        history = payload["input"]
        check_pairs(history)
        question = history[0]["content"]
        calls = {i["call_id"]: i for i in history if i.get("type") == "function_call"}
        results = [i for i in history if i.get("type") == "function_call_output"]
        searched = [
            json.loads(c["arguments"])["query"]
            for c in calls.values()
            if c["name"] == "search_notes"
        ]
        first = self.query or first_word(question)

        if self.stubborn:
            return tool_call(f"search-{self.calls}", "search_notes", {"query": first})
        if not results:
            return tool_call("search-1", self.tool_name, {"query": first})

        last_call = calls[results[-1]["call_id"]]
        last_result = json.loads(results[-1]["output"])

        if last_call["name"] == "save_email_draft":
            if last_result.get("saved"):
                return message(
                    "The approved draft was saved locally. No email was sent."
                )
            return message("You did not approve the draft, so I did not save it.")

        matches = last_result["matches"]
        if not matches:
            # An empty result is information: try another word from the question.
            untried = [w for w in words_in(question) if w not in searched]
            if untried:
                call_id = f"search-{len(searched) + 1}"
                return tool_call(call_id, "search_notes", {"query": untried[0]})
            return message(f"I searched for {', '.join(searched)} and found no note.")

        texts = [note["text"] for note in matches]
        if self.email:
            body = "Here is what I found in the notes:\n" + "\n".join(
                f"- {text}" for text in texts
            )
            draft = {"to": "learner@example.invalid", "subject": "Notes found"}
            return tool_call("draft-1", "save_email_draft", {**draft, "body": body})
        return message("Found notes:\n" + "\n".join(texts))
