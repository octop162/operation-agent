"""AgentCore Runtime 動作確認スクリプト

使い方:
    uv run python test_agentcore.py
    uv run python test_agentcore.py "カスタムプロンプト"
    uv run python test_agentcore.py --env prod "プロンプト"
"""

import argparse
import json
import sys
import uuid

import boto3

REGION = "ap-northeast-1"
RUNTIME_NAME_TEMPLATE = "operation_agent_{env}"


def get_runtime_arn(env: str) -> str:
    client = boto3.client("bedrock-agentcore-control", region_name=REGION)
    runtime_name = RUNTIME_NAME_TEMPLATE.format(env=env)

    paginator = client.get_paginator("list_agent_runtimes")
    for page in paginator.paginate():
        for runtime in page.get("agentRuntimes", []):
            if runtime["agentRuntimeName"] == runtime_name:
                return runtime["agentRuntimeArn"]

    raise ValueError(f"AgentCore Runtime '{runtime_name}' が見つかりません (region={REGION})")


def invoke(runtime_arn: str, prompt: str) -> dict:
    client = boto3.client("bedrock-agentcore", region_name=REGION)
    session_id = uuid.uuid4().hex + uuid.uuid4().hex[:5]  # 33文字以上

    response = client.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        runtimeSessionId=session_id,
        payload=json.dumps({"prompt": prompt}).encode(),
        qualifier="DEFAULT",
    )
    return json.loads(response["response"].read())


def main() -> None:
    parser = argparse.ArgumentParser(description="AgentCore Runtime 動作確認")
    parser.add_argument("prompt", nargs="?", default="こんにちは。あなたは何ができますか？")
    parser.add_argument("--env", default="dev", choices=["dev", "prod"])
    args = parser.parse_args()

    print(f"[AgentCore] env={args.env}, prompt={args.prompt!r}")
    print("Runtime ARN を取得中...")
    arn = get_runtime_arn(args.env)
    print(f"ARN: {arn}")

    print("Invoking...")
    result = invoke(arn, args.prompt)
    print("\n=== レスポンス ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
