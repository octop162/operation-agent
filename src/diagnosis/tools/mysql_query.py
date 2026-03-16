import json

import boto3
from botocore.exceptions import ClientError
from strands import tool

from diagnosis.config import DiagnosisConfig


@tool
def mysql_query(sql: str) -> str:
    """MySQLデータベースにSQLクエリを実行し、結果を返す。

    AWS Lambda 経由でMySQLに接続する。Lambda側で接続・認証を管理する。
    ペイロードとして {"sql": "<クエリ>"} を送信し、結果をJSON文字列で返す。

    Args:
        sql: 実行するSQLクエリ文字列（例: "SELECT id, name FROM users LIMIT 10"）

    Returns:
        クエリ結果をJSON文字列として返す。
    """
    config = DiagnosisConfig()

    if not config.mysql_lambda_function:
        raise RuntimeError(
            "DIAG_MYSQL_LAMBDA_FUNCTION is not configured. Set the environment variable to the Lambda function name."
        )

    client = boto3.client("lambda", region_name=config.aws_region)

    try:
        response = client.invoke(
            FunctionName=config.mysql_lambda_function,
            InvocationType="RequestResponse",
            Payload=json.dumps({"sql": sql}).encode(),
        )
    except ClientError as exc:
        raise RuntimeError(f"Lambda invocation failed: {exc.response['Error']['Message']}") from exc

    if response.get("FunctionError"):
        raw = response["Payload"].read()
        try:
            detail = json.loads(raw).get("errorMessage", raw.decode())
        except (json.JSONDecodeError, AttributeError):
            detail = raw.decode(errors="replace")
        raise RuntimeError(f"Lambda function error: {detail}")

    return json.dumps(json.loads(response["Payload"].read()), ensure_ascii=False, indent=2)
