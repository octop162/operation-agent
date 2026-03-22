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

# deploy.sh --slack が AWS CLI で取得した ARN を環境変数で渡す
agent_runtime_arn = os.environ.get("AGENT_RUNTIME_ARN", "")

SlackBotStack(
    app,
    f"SlackBot{env_name.capitalize()}Stack",
    env_name=env_name,
    agent_runtime_arn=agent_runtime_arn,
    env=cdk_env,
)

app.synth()
