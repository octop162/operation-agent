"""slack_bot.app のハンドラロジックのユニットテスト。

Bolt App の初期化は環境変数が必要なため、モジュールレベルの import を避けて
ハンドラ関数を直接テストする。
"""

from unittest.mock import MagicMock, patch


def _make_event(text="<@BOT> 調査して", ts="1234567890.123456", thread_ts=None, channel="C123"):
    event = {"text": text, "ts": ts, "channel": channel, "user": "U456"}
    if thread_ts:
        event["thread_ts"] = thread_ts
    return event


def test_handle_mention_calls_ack():
    from slack_bot.app import handle_mention

    ack = MagicMock()
    handle_mention(ack)
    ack.assert_called_once()


def test_process_mention_posts_investigating_message():
    from slack_bot.app import process_mention

    say = MagicMock(return_value={"ts": "ts_investigating"})
    client = MagicMock()
    client.conversations_replies.return_value = {"messages": []}

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.return_value = "診断結果"
        mock_get.return_value = agent_client

        process_mention(say=say, event=_make_event(), client=client)

    say.assert_any_call(text="調査中...", thread_ts="1234567890.123456")


def test_process_mention_replies_in_thread_with_thread_ts():
    from slack_bot.app import process_mention

    say = MagicMock(return_value={"ts": "ts_investigating"})
    client = MagicMock()
    client.conversations_replies.return_value = {"messages": []}

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.return_value = "結果"
        mock_get.return_value = agent_client

        process_mention(say=say, event=_make_event(thread_ts="9999.111"), client=client)

    say.assert_any_call(text="調査中...", thread_ts="9999.111")


def test_process_mention_updates_investigating_message():
    from slack_bot.app import process_mention

    say = MagicMock(return_value={"ts": "ts_investigating"})
    client = MagicMock()
    client.conversations_replies.return_value = {"messages": []}

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.return_value = "最終診断結果"
        mock_get.return_value = agent_client

        process_mention(say=say, event=_make_event(), client=client)

    client.chat_update.assert_called_once()
    call_kwargs = client.chat_update.call_args[1]
    assert call_kwargs["text"] == "最終診断結果"
    assert call_kwargs["ts"] == "ts_investigating"


def test_process_mention_invokes_agent_with_prompt():
    from slack_bot.app import process_mention

    say = MagicMock(return_value={"ts": "ts_investigating"})
    client = MagicMock()
    client.conversations_replies.return_value = {"messages": []}

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.return_value = "OK"
        mock_get.return_value = agent_client

        process_mention(say=say, event=_make_event(text="<@BOT> DBが重い"), client=client)

    agent_client.invoke.assert_called_once()
    call_kwargs = agent_client.invoke.call_args[1]
    assert "DBが重い" in call_kwargs["prompt"] or "DBが重い" in str(agent_client.invoke.call_args)


def test_process_mention_handles_agent_error_gracefully():
    from slack_bot.app import process_mention

    say = MagicMock(return_value={"ts": "ts_investigating"})
    client = MagicMock()
    client.conversations_replies.return_value = {"messages": []}

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.side_effect = RuntimeError("connection failed")
        mock_get.return_value = agent_client

        # エラーが外に伝播しないこと
        process_mention(say=say, event=_make_event(), client=client)

    call_kwargs = client.chat_update.call_args[1]
    assert "エラー" in call_kwargs["text"]


def test_make_session_id_is_deterministic():
    from slack_bot.app import _make_session_id

    s1 = _make_session_id("C123", "1234567890.123456")
    s2 = _make_session_id("C123", "1234567890.123456")
    assert s1 == s2


def test_make_session_id_is_at_least_33_chars():
    from slack_bot.app import _make_session_id

    session_id = _make_session_id("C123", "1234567890.123456")
    assert len(session_id) >= 33
