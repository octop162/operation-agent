import pytest
from pydantic import ValidationError


def test_config_defaults():
    from diagnosis.config import DiagnosisConfig

    config = DiagnosisConfig()
    assert config.model_id == "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    assert config.aws_region == "ap-northeast-1"
    assert config.max_tokens == 4096
    assert isinstance(config.temperature, float)


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("DIAG_MODEL_ID", "us.anthropic.claude-opus-4-20250514")
    monkeypatch.setenv("DIAG_AWS_REGION", "us-east-1")
    monkeypatch.setenv("DIAG_MAX_TOKENS", "8192")
    monkeypatch.setenv("DIAG_TEMPERATURE", "0.5")

    # pydantic-settings はモジュールキャッシュを持つためインポートし直す
    import importlib

    import diagnosis.config as cfg_module

    importlib.reload(cfg_module)
    from diagnosis.config import DiagnosisConfig

    config = DiagnosisConfig()
    assert config.model_id == "us.anthropic.claude-opus-4-20250514"
    assert config.aws_region == "us-east-1"
    assert config.max_tokens == 8192
    assert config.temperature == pytest.approx(0.5)


def test_config_invalid_temperature(monkeypatch):
    monkeypatch.setenv("DIAG_TEMPERATURE", "not-a-float")

    import importlib

    import diagnosis.config as cfg_module

    importlib.reload(cfg_module)
    from diagnosis.config import DiagnosisConfig

    with pytest.raises((ValidationError, ValueError)):
        DiagnosisConfig()
