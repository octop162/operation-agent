import os

import aws_cdk as cdk
import aws_cdk.aws_apigatewayv2 as apigwv2
import aws_cdk.aws_apigatewayv2_integrations as integrations
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
from constructs import Construct

REGION = "ap-northeast-1"


class SlackBotStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_name: str = "dev",
        agent_runtime_arn: str,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        removal_policy = cdk.RemovalPolicy.RETAIN if env_name == "prod" else cdk.RemovalPolicy.DESTROY

        # Slack トークンは SSM SecureString で管理 (デプロイ前に手動作成)
        # CFn は Lambda 環境変数への SSM_SECURE dynamic reference を未サポートのため、
        # パラメータ名を渡して Lambda 起動時に boto3 で取得する方式を採用
        bot_token_param = f"/operation-agent/{env_name}/slack/bot-token"
        signing_secret_param = f"/operation-agent/{env_name}/slack/signing-secret"

        # Lambda 関数
        slack_fn = lambda_.Function(
            self,
            "SlackBotFunction",
            function_name=f"operation-agent-slack-bot-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.ARM_64,
            handler="slack_bot.handler.handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "../../src/slack_bot"),
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install slack-bolt -t /asset-output"
                        " && mkdir -p /asset-output/slack_bot"
                        " && cp -r /asset-input/. /asset-output/slack_bot/",
                    ],
                ),
            ),
            timeout=cdk.Duration.minutes(15),
            memory_size=512,
            environment={
                "SLACK_BOT_TOKEN_PARAM": bot_token_param,
                "SLACK_SIGNING_SECRET_PARAM": signing_secret_param,
                "AGENT_RUNTIME_ARN": agent_runtime_arn,
            },
        )
        slack_fn.apply_removal_policy(removal_policy)

        # SSM SecureString パラメータの読み取り権限
        slack_fn.add_to_role_policy(
            iam.PolicyStatement(
                sid="SsmGetSlackSecrets",
                effect=iam.Effect.ALLOW,
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:{REGION}:{self.account}:parameter{bot_token_param}",
                    f"arn:aws:ssm:{REGION}:{self.account}:parameter{signing_secret_param}",
                ],
            )
        )

        # lazy listener が自分自身を非同期 invoke するために必要
        # function_arn を直接参照すると循環依存になるため format_arn で構築する
        self_arn = self.format_arn(
            service="lambda",
            resource="function",
            resource_name=f"operation-agent-slack-bot-{env_name}",
            arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME,
        )
        slack_fn.add_to_role_policy(
            iam.PolicyStatement(
                sid="SelfInvoke",
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[self_arn],
            )
        )

        # AgentCore Runtime の呼び出し権限
        slack_fn.add_to_role_policy(
            iam.PolicyStatement(
                sid="AgentCoreInvoke",
                effect=iam.Effect.ALLOW,
                actions=["bedrock-agentcore:InvokeAgentRuntime"],
                resources=[f"arn:aws:bedrock-agentcore:{REGION}:{self.account}:runtime/*"],
            )
        )

        # API Gateway HTTP API v2
        http_api = apigwv2.HttpApi(
            self,
            "SlackBotApi",
            api_name=f"operation-agent-slack-{env_name}",
        )
        http_api.add_routes(
            path="/slack/events",
            methods=[apigwv2.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration("SlackBotIntegration", slack_fn),
        )

        cdk.CfnOutput(
            self,
            "SlackEndpointUrl",
            value=f"{http_api.api_endpoint}/slack/events",
            description="Slack Event Subscriptions の Request URL に設定してください",
        )
