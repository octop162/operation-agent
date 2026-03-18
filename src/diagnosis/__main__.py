"""AgentCore Runtime エントリポイント — HTTP サーバとして動作する"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from diagnosis.agent import create_agent
from diagnosis.telemetry import setup_telemetry

setup_telemetry()

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
