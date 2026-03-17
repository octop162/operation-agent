import os

import aws_cdk as cdk
import aws_cdk.aws_bedrock_agentcore_alpha as agentcore
import aws_cdk.aws_iam as iam
from constructs import Construct

REGION = "ap-northeast-1"


class OperationAgentStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, *, env_name: str = "dev", **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        removal_policy = cdk.RemovalPolicy.RETAIN if env_name == "prod" else cdk.RemovalPolicy.DESTROY

        # -------------------------------------------------------------------
        # AgentCore Runtime 用 IAM ロール
        # -------------------------------------------------------------------
        agent_role = iam.Role(
            self,
            "AgentRuntimeRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description=f"Execution role for operation-agent AgentCore Runtime ({env_name})",
        )
        agent_role.apply_removal_policy(removal_policy)

        # Bedrock モデル呼び出し権限
        agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockInvokeModel",
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[f"arn:aws:bedrock:{REGION}::foundation-model/anthropic.claude-*"],
            )
        )

        # CloudWatch Logs Insights 権限
        agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogsInsights",
                effect=iam.Effect.ALLOW,
                actions=["logs:StartQuery", "logs:GetQueryResults"],
                resources=[f"arn:aws:logs:{REGION}:*:log-group:*"],
            )
        )

        # -------------------------------------------------------------------
        # AgentCore Runtime
        # -------------------------------------------------------------------
        # Dockerfile はプロジェクトルート (infra/ の 2 階層上) に置く
        project_root = os.path.join(os.path.dirname(__file__), "../..")
        artifact = agentcore.AgentRuntimeArtifact.from_asset(project_root)

        agentcore.Runtime(
            self,
            "AgentRuntime",
            runtime_name=f"operation_agent_{env_name}",
            agent_runtime_artifact=artifact,
            execution_role=agent_role,
            description=f"operation-agent Strands Agents runtime ({env_name})",
        )
