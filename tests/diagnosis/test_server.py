from unittest.mock import MagicMock, patch


def test_handle_passes_prompt_to_agent():
    """_handle はペイロードの prompt をエージェントに渡す"""
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: "CPU スパイクはキャッシュ不足が原因です"
    mock_agent = MagicMock(return_value=mock_result)

    with patch("diagnosis.__main__._get_agent", return_value=mock_agent):
        from diagnosis.__main__ import _handle

        result = _handle({"prompt": "サーバAでCPUスパイク"})

    mock_agent.assert_called_once_with("サーバAでCPUスパイク")
    assert result == {"result": "CPU スパイクはキャッシュ不足が原因です"}


def test_handle_uses_empty_string_when_prompt_missing():
    """_handle は prompt キーがない場合、空文字列をエージェントに渡す"""
    mock_agent = MagicMock(return_value=MagicMock(__str__=lambda self: ""))

    with patch("diagnosis.__main__._get_agent", return_value=mock_agent):
        from diagnosis.__main__ import _handle

        _handle({})

    mock_agent.assert_called_once_with("")


def test_handle_returns_string_result():
    """_handle は結果を {"result": str} 形式で返す"""
    mock_agent = MagicMock(return_value=MagicMock(__str__=lambda self: "42"))

    with patch("diagnosis.__main__._get_agent", return_value=mock_agent):
        from diagnosis.__main__ import _handle

        result = _handle({"prompt": "test"})

    assert isinstance(result, dict)
    assert "result" in result
    assert result["result"] == "42"
