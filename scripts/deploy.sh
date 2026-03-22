#!/usr/bin/env bash
# デプロイスクリプト
# 使用方法:
#   ./scripts/deploy.sh dev            # AgentCore のみ
#   ./scripts/deploy.sh dev --slack    # Slack Bot のみ
#   ./scripts/deploy.sh dev --all      # AgentCore + Slack Bot
set -euo pipefail

ENV="${1:-dev}"
TARGET="${2:---agent}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    echo "ERROR: 環境は 'dev' または 'prod' を指定してください"
    echo "使用方法: $0 [dev|prod] [--agent|--slack|--all]"
    exit 1
fi

# 前提チェック
if ! aws sts get-caller-identity &>/dev/null; then
    echo "ERROR: AWS 認証情報が設定されていません"
    exit 1
fi

cd "$PROJECT_ROOT/infra"
echo "--- CDK 依存インストール ---"
uv pip install -r requirements.txt -q

deploy_agent() {
    echo "=== AgentCore デプロイ (env=${ENV}) ==="
    npx aws-cdk deploy "OperationAgent${ENV^}Stack" --context "env=${ENV}" --require-approval never
    echo "=== AgentCore デプロイ完了 ==="
}

get_runtime_arn() {
    aws bedrock-agentcore-control list-agent-runtimes \
        --region ap-northeast-1 \
        --query "agentRuntimes[?agentRuntimeName=='operation_agent_${ENV}'].agentRuntimeArn | [0]" \
        --output text
}

deploy_slack() {
    echo "=== Slack Bot デプロイ (env=${ENV}) ==="
    echo "--- Runtime ARN 取得中 ---"
    AGENT_RUNTIME_ARN=$(get_runtime_arn)
    if [[ -z "$AGENT_RUNTIME_ARN" || "$AGENT_RUNTIME_ARN" == "None" ]]; then
        echo "ERROR: AgentCore Runtime 'operation_agent_${ENV}' が見つかりません"
        echo "先に AgentCore をデプロイしてください: $0 ${ENV}"
        exit 1
    fi
    echo "ARN: ${AGENT_RUNTIME_ARN}"
    AGENT_RUNTIME_ARN="$AGENT_RUNTIME_ARN" npx aws-cdk deploy "SlackBot${ENV^}Stack" --context "env=${ENV}" --require-approval never
    echo "=== Slack Bot デプロイ完了 ==="
}

case "$TARGET" in
    --agent)
        deploy_agent
        ;;
    --slack)
        deploy_slack
        ;;
    --all)
        deploy_agent
        deploy_slack
        ;;
    *)
        echo "ERROR: 不明なオプション: $TARGET"
        echo "使用方法: $0 [dev|prod] [--agent|--slack|--all]"
        exit 1
        ;;
esac
