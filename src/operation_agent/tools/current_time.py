import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from strands import tool


@tool
def get_current_time() -> str:
    """現在の日時を返す。cwl_insights の start_time/end_time を計算するときに使う。

    Returns:
        現在時刻をJSON文字列で返す。
        {"unix_seconds": int, "utc": str, "jst": str}
    """
    now_utc = datetime.now(timezone.utc)
    return json.dumps(
        {
            "unix_seconds": int(now_utc.timestamp()),
            "utc": now_utc.isoformat(),
            "jst": now_utc.astimezone(ZoneInfo("Asia/Tokyo")).isoformat(),
        },
        ensure_ascii=False,
    )
