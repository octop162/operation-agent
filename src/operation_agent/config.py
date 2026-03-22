from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENT_")
    model_id: str = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    aws_region: str = "ap-northeast-1"
    max_tokens: int = 4096
    temperature: float = 0.1
    notion_api_token: str = ""
    session_bucket: str = ""
