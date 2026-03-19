import logging
import os

import boto3
from slack_bolt import App

from slack_bot.agent_client import AgentCoreClient

logger = logging.getLogger(__name__)


def _resolve_secret(param_env: str, direct_env: str, default: str = "dummy") -> str:
    """SSM パラメータ名が環境変数にある場合は SSM から取得し、なければ直接環境変数を参照する。"""
    param_name = os.environ.get(param_env)
    if param_name:
        ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "ap-northeast-1"))
        resp = ssm.get_parameter(Name=param_name, WithDecryption=True)
        return resp["Parameter"]["Value"]
    return os.environ.get(direct_env, default)


app = App(
    token=_resolve_secret("SLACK_BOT_TOKEN_PARAM", "SLACK_BOT_TOKEN"),
    signing_secret=_resolve_secret("SLACK_SIGNING_SECRET_PARAM", "SLACK_SIGNING_SECRET"),
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


def handle_reaction_added(ack) -> None:  # type: ignore[no-untyped-def]
    """Slack の 3 秒タイムアウト回避のために即時 ACK を返す。"""
    ack()


def process_reaction_added(event, client, say) -> None:  # type: ignore[no-untyped-def]
    """:eyes: リアクションを受けたメッセージを診断する (lazy listener で非同期実行)。"""
    if event.get("reaction") != "eyes":
        return

    item = event["item"]
    channel = item["channel"]
    ts = item["ts"]

    # リアクションされたメッセージ本文を取得
    resp = client.conversations_history(channel=channel, latest=ts, limit=1, inclusive=True)
    messages = resp.get("messages", [])
    prompt = messages[0].get("text", "") if messages else ""

    # 先に「調査中...」を投稿して ts を保存
    posted = say(text="調査中...", thread_ts=ts)
    investigating_ts = posted["ts"]

    session_id = _make_session_id(channel, ts)
    try:
        result = _get_agent_client().invoke(prompt=prompt, session_id=session_id)
    except Exception as exc:
        logger.exception("AgentCore の呼び出しに失敗しました")
        result = f"エラーが発生しました: {exc}"

    client.chat_update(channel=channel, ts=investigating_ts, text=result)


app.event("app_mention")(ack=handle_mention, lazy=[process_mention])
app.event("reaction_added")(ack=handle_reaction_added, lazy=[process_reaction_added])
