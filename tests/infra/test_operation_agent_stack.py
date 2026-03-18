import os
import sys

# infra/ をパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../infra"))

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template
from stacks.operation_agent_stack import OperationAgentStack


def make_stack(env_name: str = "dev") -> OperationAgentStack:
    app = cdk.App(context={"env": env_name})
    return OperationAgentStack(app, "TestStack", env_name=env_name)


def test_agentcore_runtime_exists():
    template = Template.from_stack(make_stack())
    template.resource_count_is("AWS::BedrockAgentCore::Runtime", 1)


def test_agentcore_runtime_name_dev():
    template = Template.from_stack(make_stack("dev"))
    template.has_resource_properties(
        "AWS::BedrockAgentCore::Runtime",
        {"AgentRuntimeName": "operation_agent_dev"},
    )


def test_agentcore_runtime_name_prod():
    template = Template.from_stack(make_stack("prod"))
    template.has_resource_properties(
        "AWS::BedrockAgentCore::Runtime",
        {"AgentRuntimeName": "operation_agent_prod"},
    )


def test_iam_role_has_bedrock_permission():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                                "Effect": "Allow",
                            }
                        )
                    ]
                )
            }
        },
    )


def test_iam_role_has_cloudwatch_logs_permission():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [Match.object_like({"Action": ["logs:StartQuery", "logs:GetQueryResults"], "Effect": "Allow"})]
                )
            }
        },
    )


def test_prod_iam_role_uses_retain_policy():
    template = Template.from_stack(make_stack("prod"))
    template.has_resource(
        "AWS::IAM::Role",
        {"DeletionPolicy": "Retain"},
    )


def test_dev_iam_role_uses_delete_policy():
    template = Template.from_stack(make_stack("dev"))
    template.has_resource(
        "AWS::IAM::Role",
        {"DeletionPolicy": "Delete"},
    )


def test_session_bucket_exists():
    template = Template.from_stack(make_stack())
    template.resource_count_is("AWS::S3::Bucket", 1)


def test_session_bucket_uses_delete_policy_in_dev():
    template = Template.from_stack(make_stack("dev"))
    template.has_resource("AWS::S3::Bucket", {"DeletionPolicy": "Delete"})


def test_session_bucket_uses_retain_policy_in_prod():
    template = Template.from_stack(make_stack("prod"))
    template.has_resource("AWS::S3::Bucket", {"DeletionPolicy": "Retain"})


def test_iam_role_has_s3_session_permission():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Action": Match.array_with(["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]),
                                "Effect": "Allow",
                            }
                        )
                    ]
                )
            }
        },
    )


def test_agentcore_runtime_has_session_bucket_env():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::BedrockAgentCore::Runtime",
        {"EnvironmentVariables": Match.object_like({"DIAG_SESSION_BUCKET": Match.any_value()})},
    )


def test_agentcore_runtime_has_notion_api_token_param_env():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::BedrockAgentCore::Runtime",
        {
            "EnvironmentVariables": Match.object_like(
                {"DIAG_NOTION_API_TOKEN_PARAM": "/operation-agent/dev/notion/api-key"}
            )
        },
    )


def test_iam_role_has_ssm_notion_permission():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Sid": "SsmGetNotionApiKey",
                                "Action": "ssm:GetParameter",
                                "Effect": "Allow",
                            }
                        )
                    ]
                )
            }
        },
    )
