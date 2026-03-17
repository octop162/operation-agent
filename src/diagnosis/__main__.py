"""AgentCore Runtime エントリポイント — HTTP サーバとして動作する"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from diagnosis.agent import create_agent

app = BedrockAgentCoreApp()

_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def _handle(payload: dict) -> dict:
    user_message = payload.get("prompt", "")
    result = _get_agent()(user_message)
    return {"result": str(result)}


@app.entrypoint
def invoke(payload: dict) -> dict:
    return _handle(payload)


if __name__ == "__main__":
    app.run()
