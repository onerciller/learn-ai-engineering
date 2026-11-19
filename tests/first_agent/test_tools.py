from pathlib import Path

import pytest

from tutorials.first_agent.tools import search_notes


def test_search_matches_title_without_case_or_outer_space() -> None:
    result = search_notes("  LAUNCH  ")
    assert [note["id"] for note in result["matches"]] == ["launch"]
    assert "support scope is unclear" in result["matches"][0]["text"]


def test_search_matches_body_and_returns_all_matches() -> None:
    assert [note["id"] for note in search_notes("support")["matches"]] == [
        "launch",
        "hiring",
    ]


def test_missing_notes_are_an_empty_result() -> None:
    assert search_notes("no-matching-note-123") == {"matches": []}


@pytest.mark.parametrize("query", ["", "  ", None, 42, {"query": "launch"}])
def test_invalid_query_is_rejected(query: object) -> None:
    with pytest.raises(ValueError, match="non-empty string"):
        search_notes(query)  # type: ignore[arg-type]


def test_sample_data_path_does_not_depend_on_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert search_notes("launch")["matches"][0]["id"] == "launch"
