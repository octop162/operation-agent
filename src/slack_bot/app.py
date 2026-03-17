import logging
import os

from slack_bolt import App

from slack_bot.agent_client import AgentCoreClient

logger = logging.getLogger(__name__)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN", "dummy"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET", "dummy"),
    process_before_response=True,
    token_verification_enabled=False,
)

_agent_client: AgentCoreClient | None = None


def _get_agent_client() -> AgentCoreClient:
    global _agent_client
    if _agent_client is None:
        _agent_client = AgentCoreClient()
    return _agent_client


def _make_session_id(channel: str, thread_ts: str) -> str:
    """Slack のチャンネル + スレッド ts から AgentCore セッション ID を生成する。

    runtimeSessionId は 33 文字以上必要。
    """
    raw = f"{channel}_{thread_ts}".replace(".", "")
    return raw[:50].ljust(33, "0")


def handle_mention(ack) -> None:  # type: ignore[no-untyped-def]
    """Slack の 3 秒タイムアウト回避のために即時 ACK を返す。"""
    ack()


def process_mention(say, event, client) -> None:  # type: ignore[no-untyped-def]
    """エージェントを呼び出して診断結果をスレッドに返す (lazy listener で非同期実行)。"""
    channel = event["channel"]
    thread_ts = event.get("thread_ts") or event["ts"]

    # 先に「調査中...」を投稿して ts を保存
    posted = say(text="調査中...", thread_ts=thread_ts)
    investigating_ts = posted["ts"]

    # スレッド履歴からコンテキストを構築
    try:
        history = client.conversations_replies(channel=channel, ts=thread_ts)
        messages = history.get("messages", [])
        context_lines = [
            f"{m.get('user', 'bot')}: {m.get('text', '')}"
            for m in messages[-10:]
            if m.get("text") and not m.get("text", "").startswith("調査中")
        ]
        prompt = "\n".join(context_lines) if len(context_lines) > 1 else event.get("text", "")
    except Exception:
        logger.exception("スレッド履歴の取得に失敗しました")
        prompt = event.get("text", "")

    # AgentCore Runtime を呼び出し
    session_id = _make_session_id(channel, thread_ts)
    try:
        result = _get_agent_client().invoke(prompt=prompt, session_id=session_id)
    except Exception as exc:
        logger.exception("AgentCore の呼び出しに失敗しました")
        result = f"エラーが発生しました: {exc}"

    # 「調査中...」メッセージを診断結果で更新
    client.chat_update(channel=channel, ts=investigating_ts, text=result)


app.event("app_mention")(ack=handle_mention, lazy=[process_mention])
