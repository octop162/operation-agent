import os

import aws_cdk as cdk
import aws_cdk.aws_bedrock_agentcore_alpha as agentcore
import aws_cdk.aws_ecr_assets as ecr_assets  # noqa: F401 – used via agentcore.AgentRuntimeArtifact.from_asset
import aws_cdk.aws_iam as iam
import aws_cdk.aws_s3 as s3
from constructs import Construct

REGION = "ap-northeast-1"


class OperationAgentStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, *, env_name: str = "dev", **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        removal_policy = cdk.RemovalPolicy.RETAIN if env_name == "prod" else cdk.RemovalPolicy.DESTROY

        # -------------------------------------------------------------------
        # S3 セッションバケット（会話履歴の永続化）
        # -------------------------------------------------------------------
        session_bucket = s3.Bucket(
            self,
            "SessionBucket",
            removal_policy=removal_policy,
            auto_delete_objects=removal_policy == cdk.RemovalPolicy.DESTROY,
        )

        # -------------------------------------------------------------------
        # AgentCore Runtime 用 IAM ロール
        # -------------------------------------------------------------------
        agent_role = iam.Role(
            self,
            "AgentRuntimeRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description=f"Execution role for operation-agent AgentCore Runtime ({env_name})",
        )
        agent_role.apply_removal_policy(removal_policy)

        # Bedrock モデル呼び出し権限 (InvokeModel + ConverseStream で必要な InvokeModelWithResponseStream)
        agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockInvokeModel",
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=[
                    # apac cross-region inference profile は複数リージョン (ap-northeast-1/2 など) を経由するため * を使用
                    "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                    "arn:aws:bedrock:*:*:inference-profile/*anthropic.claude-*",
                ],
            )
        )

        # X-Ray トレース権限 (ADOT による OTel トレース送信)
        agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="XRayTracing",
                effect=iam.Effect.ALLOW,
                actions=["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
                resources=["*"],
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

        # Notion API キー（SSM SecureString）読み取り権限
        notion_param = f"/operation-agent/{env_name}/notion/api-key"
        agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="SsmGetNotionApiKey",
                effect=iam.Effect.ALLOW,
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:{REGION}:{self.account}:parameter{notion_param}",
                ],
            )
        )

        # S3 セッションバケット読み書き権限
        agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3SessionReadWrite",
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
                resources=[session_bucket.arn_for_objects("*")],
            )
        )
        agent_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3SessionList",
                effect=iam.Effect.ALLOW,
                actions=["s3:ListBucket"],
                resources=[session_bucket.bucket_arn],
            )
        )

        # -------------------------------------------------------------------
        # AgentCore Runtime
        # -------------------------------------------------------------------
        # Dockerfile はプロジェクトルート (infra/ の 2 階層上) に置く
        project_root = os.path.join(os.path.dirname(__file__), "../..")
        artifact = agentcore.AgentRuntimeArtifact.from_asset(
            project_root,
            platform=ecr_assets.Platform.LINUX_ARM64,
        )

        agentcore.Runtime(
            self,
            "AgentRuntime",
            runtime_name=f"operation_agent_{env_name}",
            agent_runtime_artifact=artifact,
            execution_role=agent_role,
            description=f"operation-agent Strands Agents runtime ({env_name})",
            environment_variables={
                "OTEL_PYTHON_DISTRO": "aws_distro",
                "OTEL_PYTHON_CONFIGURATOR": "aws_configurator",
                "OTEL_SERVICE_NAME": f"operation-agent-{env_name}",
                "OTEL_EXPORTER_OTLP_ENDPOINT": f"https://xray.{REGION}.amazonaws.com",
                "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
                "DIAG_SESSION_BUCKET": session_bucket.bucket_name,
                "DIAG_NOTION_API_TOKEN_PARAM": notion_param,
            },
        )
