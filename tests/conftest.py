import pytest

from diagnosis.config import DiagnosisConfig


@pytest.fixture()
def default_config() -> DiagnosisConfig:
    return DiagnosisConfig()


@pytest.fixture()
def custom_config() -> DiagnosisConfig:
    return DiagnosisConfig(
        model_id="us.anthropic.claude-opus-4-20250514",
        aws_region="us-east-1",
        max_tokens=8192,
        temperature=0.5,
    )
