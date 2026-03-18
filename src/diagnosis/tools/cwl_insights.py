import json
import time

import boto3
from botocore.exceptions import ClientError
from strands import tool

from diagnosis.config import DiagnosisConfig

_POLL_INTERVAL_SECONDS = 1
_POLL_MAX_ATTEMPTS = 30
_TERMINAL_STATUSES = {"Complete", "Failed", "Cancelled"}

# Unix秒として妥当な上限（10桁）: ミリ秒（13桁）を誤って渡した場合に検出する
_MAX_UNIX_SECONDS = 9_999_999_999


def _validate_timestamps(start_time: int, end_time: int) -> None:
    if start_time > _MAX_UNIX_SECONDS or end_time > _MAX_UNIX_SECONDS:
        raise ValueError(
            f"start_time/end_time はUnix秒で指定してください（ミリ秒ではなく）。"
            f" 受け取った値: start_time={start_time}, end_time={end_time}"
        )
    if end_time < start_time:
        raise ValueError(
            f"end_time は start_time 以降の値を指定してください。 start_time={start_time}, end_time={end_time}"
        )


@tool
def cwl_insights(
    log_group_names: list[str],
    query_string: str,
    start_time: int,
    end_time: int,
    limit: int = 100,
) -> str:
    """CloudWatch Logs Insights でログを検索し、結果をJSON文字列で返す。

    Args:
        log_group_names: 検索対象のロググループ名リスト（例: ["/aws/lambda/my-func"]）
        query_string: CloudWatch Logs Insights クエリ文字列（例: "fields @timestamp, @message | limit 10"）
        start_time: 検索開始時刻（Unix秒）
        end_time: 検索終了時刻（Unix秒）
        limit: 返却する最大レコード数（デフォルト100）

    Returns:
        クエリ結果をJSON文字列として返す。{"status": "Complete", "results": [...], "statistics": {...}}
    """
    _validate_timestamps(start_time, end_time)
    config = DiagnosisConfig()
    client = boto3.client("logs", region_name=config.aws_region)

    try:
        response = client.start_query(
            logGroupNames=log_group_names,
            queryString=query_string,
            startTime=start_time,
            endTime=end_time,
            limit=limit,
        )
    except ClientError as exc:
        raise RuntimeError(f"CloudWatch Logs start_query failed: {exc.response['Error']['Message']}") from exc

    query_id = response["queryId"]

    for attempt in range(_POLL_MAX_ATTEMPTS):
        result = client.get_query_results(queryId=query_id)
        status = result["status"]

        if status == "Complete":
            return json.dumps(
                {"status": status, "results": result.get("results", []), "statistics": result.get("statistics", {})},
                ensure_ascii=False,
                indent=2,
            )

        if status in ("Failed", "Cancelled"):
            raise RuntimeError(f"CloudWatch Logs Insights query {status}: queryId={query_id}")

        if attempt < _POLL_MAX_ATTEMPTS - 1:
            time.sleep(_POLL_INTERVAL_SECONDS)

    raise RuntimeError(f"Timeout waiting for CloudWatch Logs Insights query: queryId={query_id}")
