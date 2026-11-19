from pathlib import Path

import pytest

from tutorials.first_agent import openrouter_client as module


def test_env_is_read_from_repo_root_not_current_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    (tmp_path / ".env").write_text(
        "OPENROUTER_API_KEY=test-key\nOPENROUTER_MODEL=provider/model\n"
    )
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    client = module.OpenRouterClient.from_env()
    assert client.api_key == "test-key"
    assert client.model == "provider/model"
    assert "test-key" not in repr(client)


def test_root_path_matches_repository():
    assert (module.REPO_ROOT / "pyproject.toml").is_file()
    assert module.REPO_ROOT == Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_timeouts_fail_before_network(timeout):
    with pytest.raises(ValueError, match="Timeout"):
        module.OpenRouterClient("test-key", "provider/model").create_response(
            {}, timeout_seconds=timeout
        )
