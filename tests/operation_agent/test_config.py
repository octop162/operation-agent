import pytest
from pydantic import ValidationError


def test_config_defaults():
    from operation_agent.config import AgentConfig

    config = AgentConfig()
    assert config.model_id == "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    assert config.aws_region == "ap-northeast-1"
    assert config.max_tokens == 4096
    assert isinstance(config.temperature, float)


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("AGENT_MODEL_ID", "us.anthropic.claude-opus-4-20250514")
    monkeypatch.setenv("AGENT_AWS_REGION", "us-east-1")
    monkeypatch.setenv("AGENT_MAX_TOKENS", "8192")
    monkeypatch.setenv("AGENT_TEMPERATURE", "0.5")

    # pydantic-settings はモジュールキャッシュを持つためインポートし直す
    import importlib

    import operation_agent.config as cfg_module

    importlib.reload(cfg_module)
    from operation_agent.config import AgentConfig

    config = AgentConfig()
    assert config.model_id == "us.anthropic.claude-opus-4-20250514"
    assert config.aws_region == "us-east-1"
    assert config.max_tokens == 8192
    assert config.temperature == pytest.approx(0.5)


def test_config_invalid_temperature(monkeypatch):
    monkeypatch.setenv("AGENT_TEMPERATURE", "not-a-float")

    import importlib

    import operation_agent.config as cfg_module

    importlib.reload(cfg_module)
    from operation_agent.config import AgentConfig

    with pytest.raises((ValidationError, ValueError)):
        AgentConfig()
