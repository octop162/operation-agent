#!/usr/bin/env python3
import os

import aws_cdk as cdk
from stacks.operation_agent_stack import OperationAgentStack

app = cdk.App()

env_name: str = app.node.try_get_context("env") or "dev"

OperationAgentStack(
    app,
    f"OperationAgent{env_name.capitalize()}Stack",
    env_name=env_name,
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="ap-northeast-1",
    ),
)

app.synth()
