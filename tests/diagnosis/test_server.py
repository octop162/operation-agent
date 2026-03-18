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
