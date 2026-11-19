"""Real Go MCP integration. Build first with make build-mcp."""

import asyncio
import os
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from tutorials.first_agent.demo import DemoModel
from tutorials.first_agent.openrouter_client import REPO_ROOT
from tutorials.first_agent.part_05.main import run
from tutorials.first_agent.protocol import AgentError


@pytest.fixture
def server():
    supplied = os.environ.get("NOTES_SERVER_BIN")
    binary = Path(supplied) if supplied else REPO_ROOT / ".bin/notes-server"
    if supplied and not binary.is_file():
        pytest.fail("NOTES_SERVER_BIN points to a missing server")
    if not binary.is_file():
        pytest.skip("Build the real Go MCP server with make build-mcp")
    return binary


class RecordingDemo(DemoModel):
    def __init__(self, query=None):
        super().__init__(query)
        self.requests = []

    def create_response(self, payload, **kwargs):
        self.requests.append(deepcopy(payload))
        return super().create_response(payload, **kwargs)


def test_real_go_server_supplies_schema_and_paired_results(server):
    model = RecordingDemo()
    result = asyncio.run(run(model, "Find tools", server=server))
    assert result.reason == "final_answer"
    assert "MCP tools offer actions" in result.answer
    tool = model.requests[0]["tools"][0]
    assert tool["name"] == "search_notes"
    assert tool["parameters"]["properties"]["query"]["type"] == "string"
    output = model.requests[1]["input"][-1]
    assert output["call_id"] == "search-1"
    assert "MCP tools offer actions" in output["output"]


def test_real_mcp_empty_search_goes_back_to_the_model(server):
    model = RecordingDemo("does-not-exist-abc")
    result = asyncio.run(run(model, "Find the MCP tools note", server=server))
    assert model.requests[1]["input"][-1]["output"] == '{"matches": []}'
    assert (result.reason, result.tool_calls) == ("final_answer", 2)
    assert "MCP tools offer actions" in result.answer


def test_mcp_tool_budget_prevents_search(server):
    result = asyncio.run(
        run(DemoModel("tools"), "Find tools", server=server, max_tools=0)
    )
    assert result.reason == "tool_limit"
    assert result.tool_calls == 0


def test_missing_binary_is_clear_error(tmp_path):
    with pytest.raises(AgentError, match="make build-mcp"):
        asyncio.run(run(DemoModel(), "Find notes", server=tmp_path / "missing"))


def test_non_mcp_process_is_closed_after_startup_failure():
    result = asyncio.run(
        run(DemoModel(), "Find notes", server=Path(sys.executable), timeout_seconds=2)
    )
    assert result.reason in {"error", "deadline"}


def test_total_deadline_includes_mcp_startup(server):
    result = asyncio.run(
        run(DemoModel(), "Find notes", server=server, timeout_seconds=0.000001)
    )
    assert result.reason == "deadline"
