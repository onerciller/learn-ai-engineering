import json
from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from tutorials.first_agent.demo import DemoModel
from tutorials.first_agent.part_01 import main as p1
from tutorials.first_agent.part_02 import main as p2
from tutorials.first_agent.part_03 import main as p3
from tutorials.first_agent.part_04 import main as p4
from tutorials.first_agent.part_04.approval import EmailDraft, ask_approval
from tutorials.first_agent.protocol import AgentError, show_history


def call(query="launch", call_id="s1", name="search_notes", arguments=None):
    return {
        "status": "completed",
        "output": [
            {
                "type": "function_call",
                "name": name,
                "call_id": call_id,
                "arguments": arguments
                if arguments is not None
                else json.dumps({"query": query}),
            }
        ],
    }


def answer(text="A final answer"):
    return {
        "status": "completed",
        "output": [
            {"type": "message", "content": [{"type": "output_text", "text": text}]}
        ],
    }


class FakeModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def create_response(self, payload, **kwargs):
        self.requests.append(deepcopy(payload))
        return deepcopy(next(self.responses))


def test_part_one_runs_one_real_search_and_stops():
    client = FakeModel([call()])
    result = p1.run(client, "Find launch")
    assert result.reason == "tool_result"
    assert "support scope is unclear" in result.answer
    assert len(client.requests) == 1


@pytest.mark.parametrize(
    "response",
    [
        call(name="delete_note"),
        call(name=["search_notes"]),
        {"status": "completed", "output": [{"type": "message", "content": [None]}]},
        call(call_id=""),
        call(arguments="not JSON"),
        call(arguments='{"query":"launch","extra":"bad"}'),
        call(arguments='{"query":""}'),
        call(arguments='{"query":42}'),
        call(arguments='{"query":"one","query":"two"}'),
        {"status": "completed", "output": []},
        {"status": "completed", "output": [{"type": "message", "content": None}]},
        {"status": "incomplete", "output": []},
        {
            "status": "completed",
            "output": [*call()["output"], *call(call_id="s2")["output"]],
        },
    ],
)
def test_part_one_rejects_invalid_requests_before_tool_execution(response, monkeypatch):
    def forbidden(query):
        pytest.fail("Invalid request executed a tool")

    monkeypatch.setattr(p1, "search_notes", forbidden)
    with pytest.raises(AgentError):
        p1.run(FakeModel([response]), "Find launch")


def test_loop_preserves_reasoning_and_pairs_real_tool_result():
    first = call()
    first["output"].insert(
        0, {"type": "reasoning", "id": "r1", "encrypted_content": "opaque"}
    )
    client = FakeModel([first, answer()])
    result = p2.run(client, "Find launch")
    continuation = client.requests[1]["input"]
    assert continuation[1] == first["output"][0]
    assert continuation[-1]["call_id"] == "s1"
    assert "support scope is unclear" in continuation[-1]["output"]
    assert result.reason == "final_answer"


def test_loop_handles_multiple_turns_and_call_ids():
    client = FakeModel([call(), call("hiring", "s2"), answer()])
    assert p2.run(client, "Find both").tool_calls == 2
    assert client.requests[2]["input"][-1]["call_id"] == "s2"


def test_empty_result_goes_back_to_the_model():
    client = FakeModel([call("unknown-123"), answer("No note matched.")])
    result = p2.run(client, "Find missing")
    assert result.reason == "final_answer"
    assert client.requests[1]["input"][-1]["output"] == '{"matches": []}'


def test_minimal_loop_matches_the_checked_loop():
    question = "Find the launch note and tell me its risk."
    assert p2.run_minimal(DemoModel(), question) == p2.run(DemoModel(), question).answer


def test_demo_model_searches_a_word_from_the_question():
    result = p2.run(DemoModel(), "Find the hiring note")
    assert "Interview two support engineers" in result.answer


def test_demo_model_retries_after_an_empty_result():
    result = p2.run(DemoModel("missing"), "Find the launch note")
    assert (result.reason, result.steps, result.tool_calls) == ("final_answer", 3, 2)
    assert "support scope is unclear" in result.answer


def test_demo_model_says_when_nothing_matches():
    result = p2.run(DemoModel(), "Find the budget note")
    assert result.answer == "I searched for budget and found no note."


def test_demo_model_rejects_a_call_without_its_result():
    history = [
        {"role": "user", "content": "Find launch"},
        {"type": "function_call", "call_id": "s1", "name": "search_notes"},
    ]
    with pytest.raises(AgentError, match="no function_call_output"):
        DemoModel().create_response({"input": history})


def test_trace_prints_each_history_item(capsys):
    p2.run(DemoModel(), "Find the launch note", trace=show_history)
    err = capsys.readouterr().err
    assert "step 2 sends 3 history item(s):" in err
    assert "function_call_output: search-1 -> " in err


def test_unchecked_version_runs_any_tool_name_the_model_chooses():
    with pytest.raises(KeyError):
        p1.run_unchecked(DemoModel(tool_name="delete_notes"), "Find launch")
    with pytest.raises(AgentError, match="not allowed"):
        p1.run(DemoModel(tool_name="delete_notes"), "Find launch")


def test_reused_call_id_is_not_executed_again():
    client = FakeModel([call(), call()])
    with pytest.raises(AgentError, match="repeated"):
        p2.run(client, "Find launch")


def test_stubborn_model_hits_the_tool_budget_first():
    result = p3.run(DemoModel(stubborn=True), "Find launch")
    assert (result.reason, result.steps, result.tool_calls) == ("tool_limit", 4, 3)


def test_step_budget_stops_repeated_requests():
    result = p3.run(
        FakeModel([call(call_id=f"s{i}") for i in range(3)]), "Find launch", max_steps=3
    )
    assert result.reason == "step_limit"
    assert result.steps == 3


def test_tool_budget_checked_before_execution():
    def forbidden(query):
        pytest.fail("Tool executed after budget exhaustion")

    result = p3.run(FakeModel([call()]), "Find launch", max_tools=0, search=forbidden)
    assert result.reason == "tool_limit"
    assert result.tool_calls == 0


def test_deadline_stops_before_tool_execution():
    times = iter([0, 0, 2])

    def forbidden(query):
        pytest.fail("Tool executed after deadline")

    result = p3.run(
        FakeModel([call()]),
        "Find launch",
        timeout_seconds=1,
        clock=lambda: next(times),
        search=forbidden,
    )
    assert result.reason == "deadline"
    assert result.tool_calls == 0


def test_tool_error_is_not_success():
    def failing(query):
        raise OSError("fixture failure")

    result = p3.run(FakeModel([call()]), "Find launch", search=failing)
    assert result.reason == "error"
    assert "fixture failure" in result.answer


def test_approved_draft_matches_preview_and_never_sends_email(tmp_path):
    previews = []
    outbox = tmp_path / "outbox.jsonl"

    def approve(preview, *, timeout_seconds):
        previews.append(json.loads(preview))
        return True

    result = p4.run(
        DemoModel(email=True),
        "Save a draft about launch",
        outbox=outbox,
        approve=approve,
    )
    assert result.reason == "final_answer"
    saved = json.loads(outbox.read_text())
    assert {k: saved[k] for k in ("to", "subject", "body")} == previews[0]
    assert saved["simulated"] is True
    assert "email_sent" not in saved


def test_rejected_draft_is_reported_to_the_model_and_not_saved(tmp_path):
    outbox = tmp_path / "outbox.jsonl"
    result = p4.run(
        DemoModel(email=True),
        "Save a draft about launch",
        outbox=outbox,
        approve=lambda preview, **kwargs: False,
    )
    assert result.reason == "final_answer"
    assert "did not save" in result.answer
    assert not outbox.exists()


@pytest.mark.parametrize("reply", ["no", "", "y", "maybe", "yes please"])
def test_only_explicit_yes_is_approval(reply):
    assert ask_approval("{}", read=lambda prompt: reply) is False


def test_eof_is_rejection():
    def closed(prompt):
        raise EOFError

    assert ask_approval("{}", read=closed) is False


def test_late_approval_does_not_write(tmp_path):
    now = [0.0]

    def approve(preview, *, timeout_seconds):
        now[0] = 100
        return True

    outbox = tmp_path / "outbox.jsonl"
    result = p4.run(
        DemoModel(email=True),
        "Save a draft about launch",
        outbox=outbox,
        approve=approve,
        clock=lambda: now[0],
        timeout_seconds=1,
    )
    assert result.reason == "deadline"
    assert not outbox.exists()


def test_previewed_action_is_immutable():
    action = EmailDraft("a@example.invalid", "Subject", "Body")
    with pytest.raises(FrozenInstanceError):
        action.body = "Changed"
