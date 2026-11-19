"""Regression checks for work and approval after an elapsed deadline."""

from threading import Event

import pytest

from tutorials.first_agent.demo import DemoModel, message
from tutorials.first_agent.openrouter_client import OpenRouterError
from tutorials.first_agent.part_03 import main as p3
from tutorials.first_agent.part_04 import main as p4
from tutorials.first_agent.part_04.approval import ask_approval


@pytest.mark.parametrize("part", [p3, p4])
def test_late_final_answer_is_not_success(part, tmp_path):
    now = [0.0]

    class LateModel:
        def create_response(self, payload, **kwargs):
            now[0] = 2.0
            return message("Late answer")

    options = {"outbox": tmp_path / "outbox.jsonl"} if part is p4 else {}
    result = part.run(
        LateModel(), "Find launch", timeout_seconds=1, clock=lambda: now[0], **options
    )
    assert result.reason == "deadline"
    assert result.tool_calls == 0


def test_part_four_rejects_a_late_tool_before_search(tmp_path, monkeypatch):
    now = [0.0]

    class LateModel(DemoModel):
        def create_response(self, payload, **kwargs):
            response = super().create_response(payload, **kwargs)
            now[0] = 2.0
            return response

    def forbidden(query):
        pytest.fail("Search ran after the deadline")

    monkeypatch.setattr(p4, "search_notes", forbidden)
    result = p4.run(
        LateModel(),
        "Find launch",
        outbox=tmp_path / "outbox.jsonl",
        timeout_seconds=1,
        clock=lambda: now[0],
    )
    assert result.reason == "deadline"
    assert result.tool_calls == 0


@pytest.mark.parametrize("part", [p3, p4])
def test_slow_last_tool_reports_deadline_instead_of_step_limit(
    part, tmp_path, monkeypatch
):
    now = [0.0]

    def slow_search(query):
        now[0] = 2.0
        return {"matches": []}

    if part is p4:
        monkeypatch.setattr(p4, "search_notes", slow_search)
        options = {"outbox": tmp_path / "outbox.jsonl"}
    else:
        options = {"search": slow_search}
    result = part.run(
        DemoModel(),
        "Find launch",
        max_steps=1,
        timeout_seconds=1,
        clock=lambda: now[0],
        **options,
    )
    assert result.reason == "deadline"
    assert result.tool_calls == 1


@pytest.mark.parametrize("part", [p3, p4])
def test_provider_timeout_after_deadline_is_reported_as_deadline(part, tmp_path):
    now = [0.0]

    class FailingModel:
        def create_response(self, payload, **kwargs):
            now[0] = 2.0
            raise OpenRouterError("Request timed out")

    options = {"outbox": tmp_path / "outbox.jsonl"} if part is p4 else {}
    result = part.run(
        FailingModel(),
        "Find launch",
        timeout_seconds=1,
        clock=lambda: now[0],
        **options,
    )
    assert result.reason == "deadline"


def test_approval_wait_has_a_deadline():
    blocked = Event()
    try:
        with pytest.raises(TimeoutError):
            ask_approval(
                "{}", timeout_seconds=0.01, read=lambda prompt: blocked.wait(1)
            )
    finally:
        blocked.set()


def test_approval_timeout_never_saves_or_makes_another_model_request(tmp_path):
    client = DemoModel(email=True)
    outbox = tmp_path / "outbox.jsonl"
    observed = []

    def timeout(preview, *, timeout_seconds):
        observed.append(timeout_seconds)
        raise TimeoutError

    result = p4.run(
        client,
        "Save a draft about launch",
        outbox=outbox,
        approve=timeout,
        timeout_seconds=0.5,
    )
    assert result.reason == "deadline"
    assert not outbox.exists()
    assert client.calls == 2
    assert 0 < observed[0] <= 0.5


@pytest.mark.parametrize("answer", [True, False])
def test_late_approval_response_stops_before_another_action(answer, tmp_path):
    now = [0.0]
    outbox = tmp_path / "outbox.jsonl"
    client = DemoModel(email=True)

    def late_answer(preview, *, timeout_seconds):
        now[0] = 2.0
        return answer

    result = p4.run(
        client,
        "Save a draft about launch",
        outbox=outbox,
        approve=late_answer,
        timeout_seconds=1,
        clock=lambda: now[0],
    )
    assert result.reason == "deadline"
    assert not outbox.exists()
    assert client.calls == 2
