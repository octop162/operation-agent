from unittest.mock import MagicMock, patch

import pytest


def test_create_agent_returns_agent():
    from strands import Agent

    with patch("diagnosis.agent.BedrockModel") as mock_model_cls:
        mock_model_cls.return_value = MagicMock()

        from diagnosis.agent import create_agent

        agent = create_agent()

    assert isinstance(agent, Agent)


def test_create_agent_uses_config_model_id():
    from diagnosis.config import DiagnosisConfig

    config = DiagnosisConfig(model_id="us.anthropic.claude-opus-4-20250514")

    with patch("diagnosis.agent.BedrockModel") as mock_model_cls:
        mock_model_cls.return_value = MagicMock()

        from diagnosis.agent import create_agent

        create_agent(config=config)

    call_kwargs = mock_model_cls.call_args.kwargs
    assert call_kwargs["model_id"] == "us.anthropic.claude-opus-4-20250514"


def test_create_agent_uses_system_prompt():

    from diagnosis.prompts import SYSTEM_PROMPT

    with patch("diagnosis.agent.BedrockModel") as mock_model_cls:
        mock_model_cls.return_value = MagicMock()

        from diagnosis.agent import create_agent

        agent = create_agent()

    assert agent.system_prompt == SYSTEM_PROMPT


@pytest.mark.integration
def test_create_agent_integration():
    """実際のBedrockModelを使ったスモークテスト（AWS認証必要）"""
    from strands import Agent

    from diagnosis.agent import create_agent

    agent = create_agent()
    assert isinstance(agent, Agent)
