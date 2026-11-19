"""Read-only local tools used by the first four lessons."""

import json
from pathlib import Path

NOTES_PATH = Path(__file__).resolve().parent / "data" / "notes.json"
SEARCH_NOTES_TOOL = {
    "type": "function",
    "name": "search_notes",
    "description": "Search the fixed sample notes by a word in their title or text.",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string", "minLength": 1}},
        "required": ["query"],
        "additionalProperties": False,
    },
}


def search_notes(query: str) -> dict[str, list[dict[str, str]]]:
    """Return each matching note once, even if both its title and body match."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    query = query.strip().casefold()
    notes = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
    matches = []
    for note in notes:
        if query in f"{note['title']} {note['text']}".casefold():
            matches.append(note)
    return {"matches": matches}
