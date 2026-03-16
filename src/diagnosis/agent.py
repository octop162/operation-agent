from strands import Agent
from strands.models.bedrock import BedrockModel

from diagnosis.config import DiagnosisConfig
from diagnosis.prompts import SYSTEM_PROMPT


def create_agent(config: DiagnosisConfig | None = None) -> Agent:
    """障害診断エージェントを生成するファクトリ関数"""
    if config is None:
        config = DiagnosisConfig()

    model = BedrockModel(
        model_id=config.model_id,
        region_name=config.aws_region,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
    )

    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
    )
