import pytest

from operation_agent.config import AgentConfig


@pytest.fixture()
def default_config() -> AgentConfig:
    return AgentConfig()


@pytest.fixture()
def custom_config() -> AgentConfig:
    return AgentConfig(
        model_id="us.anthropic.claude-opus-4-20250514",
        aws_region="us-east-1",
        max_tokens=8192,
        temperature=0.5,
    )
