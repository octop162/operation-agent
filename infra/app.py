#!/usr/bin/env python3
import os

import aws_cdk as cdk
from stacks.operation_agent_stack import OperationAgentStack
from stacks.slack_bot_stack import SlackBotStack

app = cdk.App()

env_name: str = app.node.try_get_context("env") or "dev"

cdk_env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region="ap-northeast-1",
)

OperationAgentStack(
    app,
    f"OperationAgent{env_name.capitalize()}Stack",
    env_name=env_name,
    env=cdk_env,
)

# AgentCore Runtime の ARN は bedrock-agentcore-control API で実行時に取得するため、
# SSM 経由ではなく deploy.sh から環境変数で渡す想定
agent_runtime_arn = os.environ.get(
    "AGENT_RUNTIME_ARN",
    f"arn:aws:bedrock-agentcore:ap-northeast-1:${{AWS::AccountId}}:agent-runtime/operation_agent_{env_name}",
)

SlackBotStack(
    app,
    f"SlackBot{env_name.capitalize()}Stack",
    env_name=env_name,
    agent_runtime_arn=agent_runtime_arn,
    env=cdk_env,
)

app.synth()
