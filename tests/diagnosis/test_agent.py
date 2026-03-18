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


def test_create_agent_with_session_id_uses_s3_session_manager():
    from diagnosis.config import DiagnosisConfig

    config = DiagnosisConfig(session_bucket="my-test-bucket")

    with (
        patch("diagnosis.agent.BedrockModel") as mock_model_cls,
        patch("diagnosis.agent.S3SessionManager") as mock_sm_cls,
    ):
        mock_model_cls.return_value = MagicMock()
        mock_sm_cls.return_value = MagicMock()

        from diagnosis.agent import create_agent

        create_agent(config=config, session_id="test-session-id-12345678901234567890")

    mock_sm_cls.assert_called_once_with(
        session_id="test-session-id-12345678901234567890",
        bucket="my-test-bucket",
        prefix="sessions",
        region_name="ap-northeast-1",
    )


def test_create_agent_enables_prompt_cache():
    with patch("diagnosis.agent.BedrockModel") as mock_model_cls:
        mock_model_cls.return_value = MagicMock()

        from diagnosis.agent import create_agent

        create_agent()

    call_kwargs = mock_model_cls.call_args.kwargs
    assert call_kwargs["cache_prompt"] == "default"
    assert call_kwargs["cache_tools"] == "default"


def test_create_agent_without_session_id_skips_s3_session_manager():
    with (
        patch("diagnosis.agent.BedrockModel") as mock_model_cls,
        patch("diagnosis.agent.S3SessionManager") as mock_sm_cls,
    ):
        mock_model_cls.return_value = MagicMock()

        from diagnosis.agent import create_agent

        create_agent()

    mock_sm_cls.assert_not_called()


@pytest.mark.integration
def test_create_agent_integration():
    """実際のBedrockModelを使ったスモークテスト（AWS認証必要）"""
    from strands import Agent

    from diagnosis.agent import create_agent

    agent = create_agent()
    assert isinstance(agent, Agent)
