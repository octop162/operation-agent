from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.session.s3_session_manager import S3SessionManager

from diagnosis.config import DiagnosisConfig
from diagnosis.prompts import SYSTEM_PROMPT
from diagnosis.tools import cwl_insights, notion_search


def create_agent(config: DiagnosisConfig | None = None, session_id: str | None = None) -> Agent:
    """障害診断エージェントを生成するファクトリ関数"""
    if config is None:
        config = DiagnosisConfig()

    model = BedrockModel(
        model_id=config.model_id,
        region_name=config.aws_region,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        cache_prompt="default",
        cache_tools="default",
    )

    kwargs: dict = {}
    if session_id and config.session_bucket:
        kwargs["session_manager"] = S3SessionManager(
            session_id=session_id,
            bucket=config.session_bucket,
            prefix="sessions",
            region_name=config.aws_region,
        )

    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[notion_search, cwl_insights],
        **kwargs,
    )
