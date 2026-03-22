"""AgentCore Runtime エントリポイント — HTTP サーバとして動作する"""

import os

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from operation_agent.agent import create_agent


def _resolve_ssm_secrets() -> None:
    """SSM SecureString からシークレットを取得して環境変数にセットする。

    AGENT_NOTION_API_TOKEN_PARAM が設定されている場合、SSM から値を取得して
    AGENT_NOTION_API_TOKEN に設定する。
    """
    param_name = os.environ.get("AGENT_NOTION_API_TOKEN_PARAM")
    if param_name:
        ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "ap-northeast-1"))
        resp = ssm.get_parameter(Name=param_name, WithDecryption=True)
        os.environ["AGENT_NOTION_API_TOKEN"] = resp["Parameter"]["Value"]


_resolve_ssm_secrets()

app = BedrockAgentCoreApp()


def _handle(payload: dict) -> dict:
    user_message = payload.get("prompt", "")
    session_id = payload.get("session_id")
    agent = create_agent(session_id=session_id)
    result = agent(user_message)
    return {"result": str(result)}


@app.entrypoint
def invoke(payload: dict) -> dict:
    return _handle(payload)


if __name__ == "__main__":
    app.run()
