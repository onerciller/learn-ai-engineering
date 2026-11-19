"""Preview one immutable action, then write only after explicit approval."""

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

from tutorials.first_agent.protocol import AgentError

SAVE_DRAFT_TOOL = {
    "type": "function",
    "name": "save_email_draft",
    "description": "Save an email draft locally after user approval. Does not send email.",
    "parameters": {
        "type": "object",
        "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["to", "subject", "body"],
        "additionalProperties": False,
    },
}


@dataclass(frozen=True)
class EmailDraft:
    to: str
    subject: str
    body: str

    @classmethod
    def from_arguments(cls, arguments: dict) -> "EmailDraft":
        if set(arguments) != {"to", "subject", "body"}:
            raise AgentError("Draft requires only to, subject and body.")
        if any(not isinstance(v, str) or not v.strip() for v in arguments.values()):
            raise AgentError("Draft fields must be non-empty strings.")
        if "@" not in arguments["to"] or any(c in arguments["to"] for c in "\r\n"):
            raise AgentError("Draft recipient is invalid.")
        if (
            len(arguments["to"]) > 320
            or len(arguments["subject"]) > 200
            or len(arguments["body"]) > 5000
        ):
            raise AgentError("Draft fields are too long.")
        return cls(**arguments)

    def preview(self) -> str:
        # JSON escapes control characters in untrusted model text.
        return json.dumps(asdict(self), ensure_ascii=True, indent=2)


def ask_approval(preview: str, *, timeout_seconds: float = 30, read=input) -> bool:
    """Read an explicit yes within the wait budget; timeout never approves."""
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise TimeoutError("Approval time budget reached.")
    print("SIMULATED OUTBOX — no email will be sent.")
    print(preview)
    answers = Queue()

    def read_answer():
        try:
            answers.put(read("Save exactly this draft locally? Type yes to approve: "))
        except (EOFError, OSError):
            answers.put("")

    # This background thread only reads input. It cannot save or approve an action.
    Thread(target=read_answer, daemon=True).start()
    try:
        answer = answers.get(timeout=timeout_seconds)
    except Empty:
        raise TimeoutError("Approval time budget reached.") from None
    return answer.strip().casefold() == "yes"


def save_approved_draft(action: EmailDraft, outbox: Path) -> dict:
    """Called by the application only after approval and a fresh deadline check."""
    outbox.parent.mkdir(parents=True, exist_ok=True)
    record = {"simulated": True, "action": "save_email_draft", **asdict(action)}
    with outbox.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return {"saved": True, "simulated": True, "email_sent": False}
