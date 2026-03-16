from pydantic_settings import BaseSettings, SettingsConfigDict


class DiagnosisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DIAG_")

    model_id: str = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    aws_region: str = "ap-northeast-1"
    max_tokens: int = 4096
    temperature: float = 0.1
