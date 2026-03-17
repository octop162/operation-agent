import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from slack_bot.agent_client import AgentCoreClient


@pytest.fixture
def mock_boto3_client():
    with patch("slack_bot.agent_client.boto3.client") as mock:
        yield mock


def _make_response(result: str) -> dict:
    payload = json.dumps({"result": result}).encode()
    return {"response": BytesIO(payload)}


def test_invoke_calls_invoke_agent_runtime(mock_boto3_client):
    client_instance = MagicMock()
    mock_boto3_client.return_value = client_instance
    client_instance.invoke_agent_runtime.return_value = _make_response("OK")

    AgentCoreClient(runtime_arn="arn:test").invoke("hello", session_id="a" * 33)

    client_instance.invoke_agent_runtime.assert_called_once()


def test_invoke_sends_correct_payload(mock_boto3_client):
    client_instance = MagicMock()
    mock_boto3_client.return_value = client_instance
    client_instance.invoke_agent_runtime.return_value = _make_response("OK")

    AgentCoreClient(runtime_arn="arn:test").invoke("診断してください", session_id="a" * 33)

    call_kwargs = client_instance.invoke_agent_runtime.call_args[1]
    assert json.loads(call_kwargs["payload"]) == {"prompt": "診断してください"}
    assert call_kwargs["qualifier"] == "DEFAULT"
    assert call_kwargs["agentRuntimeArn"] == "arn:test"


def test_invoke_passes_session_id(mock_boto3_client):
    client_instance = MagicMock()
    mock_boto3_client.return_value = client_instance
    client_instance.invoke_agent_runtime.return_value = _make_response("OK")

    AgentCoreClient(runtime_arn="arn:test").invoke("hello", session_id="mysession12345678901234567890123")

    call_kwargs = client_instance.invoke_agent_runtime.call_args[1]
    assert call_kwargs["runtimeSessionId"] == "mysession12345678901234567890123"


def test_invoke_returns_result_string(mock_boto3_client):
    client_instance = MagicMock()
    mock_boto3_client.return_value = client_instance
    client_instance.invoke_agent_runtime.return_value = _make_response("診断結果です")

    result = AgentCoreClient(runtime_arn="arn:test").invoke("hello", session_id="a" * 33)

    assert result == "診断結果です"


def test_invoke_uses_env_var_for_arn(mock_boto3_client, monkeypatch):
    monkeypatch.setenv("AGENT_RUNTIME_ARN", "arn:from:env")
    client_instance = MagicMock()
    mock_boto3_client.return_value = client_instance
    client_instance.invoke_agent_runtime.return_value = _make_response("OK")

    AgentCoreClient().invoke("hello", session_id="a" * 33)

    call_kwargs = client_instance.invoke_agent_runtime.call_args[1]
    assert call_kwargs["agentRuntimeArn"] == "arn:from:env"


def test_invoke_raises_on_client_error(mock_boto3_client):
    from botocore.exceptions import ClientError

    client_instance = MagicMock()
    mock_boto3_client.return_value = client_instance
    client_instance.invoke_agent_runtime.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}}, "InvokeAgentRuntime"
    )

    with pytest.raises(ClientError):
        AgentCoreClient(runtime_arn="arn:test").invoke("hello", session_id="a" * 33)
