#!/usr/bin/env bash
# AgentCore Runtime デプロイスクリプト
# 使用方法: ./scripts/deploy.sh [dev|prod]
set -euo pipefail

ENV="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    echo "ERROR: 環境は 'dev' または 'prod' を指定してください"
    echo "使用方法: $0 [dev|prod]"
    exit 1
fi

echo "=== operation-agent デプロイ (env=${ENV}) ==="

# 前提チェック
if ! command -v cdk &>/dev/null; then
    echo "ERROR: AWS CDK CLI がインストールされていません"
    echo "  npm install -g aws-cdk"
    exit 1
fi

if ! aws sts get-caller-identity &>/dev/null; then
    echo "ERROR: AWS 認証情報が設定されていません"
    exit 1
fi

# CDK デプロイ (Dockerfile のビルド・ECR プッシュ・AgentCore Runtime 作成を含む)
cd "$PROJECT_ROOT/infra"
echo "--- CDK 依存インストール ---"
pip install -r requirements.txt -q

echo "--- デプロイ実行 ---"
cdk deploy --context "env=${ENV}" --require-approval never

echo "=== デプロイ完了 (env=${ENV}) ==="
