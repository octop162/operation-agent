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

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.return_value = "OK"
        mock_get.return_value = agent_client

        process_mention(say=say, event=_make_event(text="<@BOT> DBが重い"), client=client)

    agent_client.invoke.assert_called_once()
    call_kwargs = agent_client.invoke.call_args[1]
    assert "DBが重い" in call_kwargs["prompt"]


def test_process_mention_does_not_fetch_thread_history():
    from slack_bot.app import process_mention

    say = MagicMock(return_value={"ts": "ts_investigating"})
    client = MagicMock()

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.return_value = "OK"
        mock_get.return_value = agent_client

        process_mention(say=say, event=_make_event(), client=client)

    client.conversations_replies.assert_not_called()


def test_process_mention_handles_agent_error_gracefully():
    from slack_bot.app import process_mention

    say = MagicMock(return_value={"ts": "ts_investigating"})
    client = MagicMock()

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


# --- reaction_added ハンドラのテスト ---


def _make_reaction_event(reaction="eyes", channel="C123", ts="1234567890.123456"):
    return {
        "type": "reaction_added",
        "user": "U456",
        "reaction": reaction,
        "item": {"type": "message", "channel": channel, "ts": ts},
        "item_user": "U789",
        "event_ts": "9999.000",
    }


def test_handle_reaction_added_calls_ack():
    from slack_bot.app import handle_reaction_added

    ack = MagicMock()
    handle_reaction_added(ack)
    ack.assert_called_once()


def test_process_reaction_added_ignores_non_eyes_reaction():
    from slack_bot.app import process_reaction_added

    client = MagicMock()
    say = MagicMock()

    with patch("slack_bot.app._get_agent_client") as mock_get:
        process_reaction_added(event=_make_reaction_event(reaction="thumbsup"), client=client, say=say)
        mock_get.assert_not_called()

    client.conversations_history.assert_not_called()


def test_process_reaction_added_fetches_message_text():
    from slack_bot.app import process_reaction_added

    client = MagicMock()
    client.conversations_history.return_value = {"messages": [{"text": "DBが重い", "ts": "1234567890.123456"}]}
    say = MagicMock(return_value={"ts": "ts_investigating"})

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.return_value = "診断結果"
        mock_get.return_value = agent_client

        process_reaction_added(event=_make_reaction_event(), client=client, say=say)

    client.conversations_history.assert_called_once_with(
        channel="C123", latest="1234567890.123456", limit=1, inclusive=True
    )


def test_process_reaction_added_posts_investigating_then_updates():
    from slack_bot.app import process_reaction_added

    client = MagicMock()
    client.conversations_history.return_value = {"messages": [{"text": "DBが重い", "ts": "1234567890.123456"}]}
    say = MagicMock(return_value={"ts": "ts_investigating"})

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.return_value = "診断結果"
        mock_get.return_value = agent_client

        process_reaction_added(event=_make_reaction_event(), client=client, say=say)

    say.assert_called_once_with(text="調査中...", thread_ts="1234567890.123456")
    client.chat_update.assert_called_once()
    call_kwargs = client.chat_update.call_args[1]
    assert call_kwargs["text"] == "診断結果"
    assert call_kwargs["ts"] == "ts_investigating"


def test_process_reaction_added_invokes_agent_with_message_text():
    from slack_bot.app import process_reaction_added

    client = MagicMock()
    client.conversations_history.return_value = {"messages": [{"text": "レイテンシが高い", "ts": "1234567890.123456"}]}
    say = MagicMock(return_value={"ts": "ts_investigating"})

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.return_value = "OK"
        mock_get.return_value = agent_client

        process_reaction_added(event=_make_reaction_event(), client=client, say=say)

    call_kwargs = agent_client.invoke.call_args[1]
    assert "レイテンシが高い" in call_kwargs["prompt"]


def test_process_reaction_added_handles_agent_error_gracefully():
    from slack_bot.app import process_reaction_added

    client = MagicMock()
    client.conversations_history.return_value = {"messages": [{"text": "エラー", "ts": "1234567890.123456"}]}
    say = MagicMock(return_value={"ts": "ts_investigating"})

    with patch("slack_bot.app._get_agent_client") as mock_get:
        agent_client = MagicMock()
        agent_client.invoke.side_effect = RuntimeError("connection failed")
        mock_get.return_value = agent_client

        process_reaction_added(event=_make_reaction_event(), client=client, say=say)

    call_kwargs = client.chat_update.call_args[1]
    assert "エラー" in call_kwargs["text"]
