import json
from unittest.mock import MagicMock, patch

import pytest


def test_mysql_query_tool_exists():
    from diagnosis.tools.mysql_query import mysql_query  # noqa: F401


def test_mysql_query_is_strands_tool():
    from strands.tools.decorator import DecoratedFunctionTool

    from diagnosis.tools.mysql_query import mysql_query

    assert isinstance(mysql_query, DecoratedFunctionTool)


def test_mysql_query_returns_string_on_success(monkeypatch):
    monkeypatch.setenv("DIAG_MYSQL_LAMBDA_FUNCTION", "my-mysql-lambda")

    rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    fake_payload = MagicMock()
    fake_payload.read.return_value = json.dumps({"rows": rows}).encode()

    with patch("diagnosis.tools.mysql_query.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke.return_value = {"StatusCode": 200, "Payload": fake_payload}

        from diagnosis.tools.mysql_query import mysql_query

        result = mysql_query(sql="SELECT id, name FROM users")

    assert isinstance(result, str)
    assert "Alice" in result


def test_mysql_query_invokes_lambda_with_sql(monkeypatch):
    monkeypatch.setenv("DIAG_MYSQL_LAMBDA_FUNCTION", "test-lambda")

    fake_payload = MagicMock()
    fake_payload.read.return_value = json.dumps({"rows": []}).encode()

    with patch("diagnosis.tools.mysql_query.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke.return_value = {"StatusCode": 200, "Payload": fake_payload}

        from diagnosis.tools.mysql_query import mysql_query

        mysql_query(sql="SELECT 1")

    call_kwargs = mock_client.invoke.call_args.kwargs
    assert call_kwargs["FunctionName"] == "test-lambda"
    assert json.loads(call_kwargs["Payload"]) == {"sql": "SELECT 1"}
    assert call_kwargs["InvocationType"] == "RequestResponse"


def test_mysql_query_raises_on_lambda_function_error(monkeypatch):
    monkeypatch.setenv("DIAG_MYSQL_LAMBDA_FUNCTION", "test-lambda")

    fake_payload = MagicMock()
    fake_payload.read.return_value = json.dumps({"errorMessage": "Access denied for user"}).encode()

    with patch("diagnosis.tools.mysql_query.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke.return_value = {
            "StatusCode": 200,
            "FunctionError": "Handled",
            "Payload": fake_payload,
        }

        from diagnosis.tools.mysql_query import mysql_query

        with pytest.raises(RuntimeError, match="Access denied"):
            mysql_query(sql="SELECT secret FROM private")


def test_mysql_query_raises_on_boto_client_error(monkeypatch):
    monkeypatch.setenv("DIAG_MYSQL_LAMBDA_FUNCTION", "test-lambda")

    from botocore.exceptions import ClientError

    error_response = {"Error": {"Code": "ResourceNotFoundException", "Message": "Function not found"}}

    with patch("diagnosis.tools.mysql_query.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke.side_effect = ClientError(error_response, "Invoke")

        from diagnosis.tools.mysql_query import mysql_query

        with pytest.raises(RuntimeError, match="Function not found"):
            mysql_query(sql="SELECT 1")


def test_mysql_query_uses_region_from_config(monkeypatch):
    monkeypatch.setenv("DIAG_MYSQL_LAMBDA_FUNCTION", "test-lambda")
    monkeypatch.setenv("DIAG_AWS_REGION", "us-east-1")

    fake_payload = MagicMock()
    fake_payload.read.return_value = json.dumps({"rows": []}).encode()

    with patch("diagnosis.tools.mysql_query.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke.return_value = {"StatusCode": 200, "Payload": fake_payload}

        from diagnosis.tools.mysql_query import mysql_query

        mysql_query(sql="SELECT 1")

    mock_boto.assert_called_once_with("lambda", region_name="us-east-1")


def test_mysql_query_raises_when_function_not_configured(monkeypatch):
    monkeypatch.delenv("DIAG_MYSQL_LAMBDA_FUNCTION", raising=False)

    from diagnosis.tools.mysql_query import mysql_query

    with pytest.raises(RuntimeError, match="DIAG_MYSQL_LAMBDA_FUNCTION"):
        mysql_query(sql="SELECT 1")


@pytest.mark.integration
def test_mysql_query_integration():
    """実際のAWS LambdaへのE2Eテスト（DIAG_MYSQL_LAMBDA_FUNCTION環境変数とAWS認証必要）"""
    from diagnosis.tools.mysql_query import mysql_query

    result = mysql_query(sql="SELECT 1 AS health_check")
    assert isinstance(result, str)
    assert len(result) > 0
