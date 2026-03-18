#!/usr/bin/env bash
# AgentCore Runtime デプロイスクリプト
# 使用方法: ./scripts/deploy.sh [dev|prod]
set -euo pipefail

ENV="${1:-dev}"

export AGENT_RUNTIME_ARN=$(uv run python test_agentcore.py --env ${ENV} 2>&1 \
  | grep "^ARN:" | awk '{print $2}')
echo $AGENT_RUNTIME_ARN

cd infra
AGENT_RUNTIME_ARN=$AGENT_RUNTIME_ARN npx aws-cdk deploy SlackBot${ENV^}Stack --context env=${ENV}