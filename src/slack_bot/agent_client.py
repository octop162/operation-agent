import json
import os

import boto3

REGION = "ap-northeast-1"


class AgentCoreClient:
    def __init__(self, runtime_arn: str | None = None) -> None:
        self._runtime_arn = runtime_arn or os.environ["AGENT_RUNTIME_ARN"]
        self._client = boto3.client("bedrock-agentcore", region_name=REGION)

    def invoke(self, prompt: str, session_id: str) -> str:
        """AgentCore Runtime を呼び出して診断結果を返す。"""
        response = self._client.invoke_agent_runtime(
            agentRuntimeArn=self._runtime_arn,
            runtimeSessionId=session_id,
            payload=json.dumps({"prompt": prompt}).encode(),
            qualifier="DEFAULT",
        )
        return json.loads(response["response"].read())["result"]
