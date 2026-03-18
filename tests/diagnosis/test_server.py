import os
from unittest.mock import MagicMock, patch


def test_handle_passes_prompt_to_agent():
    """_handle はペイロードの prompt をエージェントに渡す"""
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: "CPU スパイクはキャッシュ不足が原因です"
    mock_agent = MagicMock(return_value=mock_result)

    with patch("diagnosis.__main__.create_agent", return_value=mock_agent):
        from diagnosis.__main__ import _handle

        result = _handle({"prompt": "サーバAでCPUスパイク"})

    mock_agent.assert_called_once_with("サーバAでCPUスパイク")
    assert result == {"result": "CPU スパイクはキャッシュ不足が原因です"}


def test_handle_uses_empty_string_when_prompt_missing():
    """_handle は prompt キーがない場合、空文字列をエージェントに渡す"""
    mock_agent = MagicMock(return_value=MagicMock(__str__=lambda self: ""))

    with patch("diagnosis.__main__.create_agent", return_value=mock_agent):
        from diagnosis.__main__ import _handle

        _handle({})

    mock_agent.assert_called_once_with("")


def test_handle_returns_string_result():
    """_handle は結果を {"result": str} 形式で返す"""
    mock_agent = MagicMock(return_value=MagicMock(__str__=lambda self: "42"))

    with patch("diagnosis.__main__.create_agent", return_value=mock_agent):
        from diagnosis.__main__ import _handle

        result = _handle({"prompt": "test"})

    assert isinstance(result, dict)
    assert "result" in result
    assert result["result"] == "42"


def test_handle_passes_session_id_to_create_agent():
    """_handle はペイロードの session_id を create_agent に渡す"""
    mock_agent = MagicMock(return_value=MagicMock(__str__=lambda self: "OK"))

    with patch("diagnosis.__main__.create_agent", return_value=mock_agent) as mock_create:
        from diagnosis.__main__ import _handle

        _handle({"prompt": "test", "session_id": "my-session-id"})

    mock_create.assert_called_once_with(session_id="my-session-id")


def test_handle_passes_none_session_id_when_absent():
    """_handle は session_id がない場合 None を create_agent に渡す"""
    mock_agent = MagicMock(return_value=MagicMock(__str__=lambda self: "OK"))

    with patch("diagnosis.__main__.create_agent", return_value=mock_agent) as mock_create:
        from diagnosis.__main__ import _handle

        _handle({"prompt": "test"})

    mock_create.assert_called_once_with(session_id=None)


def test_resolve_ssm_secrets_sets_env_when_param_set(monkeypatch):
    """DIAG_NOTION_API_TOKEN_PARAM が設定されている場合、SSM から取得して DIAG_NOTION_API_TOKEN をセットする"""
    from diagnosis.__main__ import _resolve_ssm_secrets  # import before patching

    monkeypatch.setenv("DIAG_NOTION_API_TOKEN_PARAM", "/operation-agent/dev/notion/api-key")
    monkeypatch.delenv("DIAG_NOTION_API_TOKEN", raising=False)

    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "secret_test_token"}}

    with patch("diagnosis.__main__.boto3") as mock_boto3:
        mock_boto3.client.return_value = mock_ssm
        _resolve_ssm_secrets()

    assert os.environ.get("DIAG_NOTION_API_TOKEN") == "secret_test_token"
    mock_ssm.get_parameter.assert_called_once_with(Name="/operation-agent/dev/notion/api-key", WithDecryption=True)


def test_resolve_ssm_secrets_noop_when_param_not_set(monkeypatch):
    """DIAG_NOTION_API_TOKEN_PARAM が未設定の場合、SSM を呼ばない"""
    from diagnosis.__main__ import _resolve_ssm_secrets  # import before patching

    monkeypatch.delenv("DIAG_NOTION_API_TOKEN_PARAM", raising=False)
    monkeypatch.delenv("DIAG_NOTION_API_TOKEN", raising=False)

    with patch("diagnosis.__main__.boto3") as mock_boto3:
        _resolve_ssm_secrets()

    mock_boto3.client.assert_not_called()
    assert os.environ.get("DIAG_NOTION_API_TOKEN") is None
