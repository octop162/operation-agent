import os
import sys

# infra/ をパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../infra"))

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template
from stacks.slack_bot_stack import SlackBotStack


def make_stack(env_name: str = "dev") -> SlackBotStack:
    app = cdk.App(context={"env": env_name})
    return SlackBotStack(
        app,
        "TestSlackBotStack",
        env_name=env_name,
        agent_runtime_arn="arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:agent-runtime/test",
    )


def test_lambda_function_exists():
    template = Template.from_stack(make_stack())
    template.resource_count_is("AWS::Lambda::Function", 1)


def test_lambda_timeout_is_15_minutes():
    template = Template.from_stack(make_stack())
    template.has_resource_properties("AWS::Lambda::Function", {"Timeout": 900})


def test_lambda_handler():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Handler": "slack_bot.handler.handler"},
    )


def test_lambda_memory_size():
    template = Template.from_stack(make_stack())
    template.has_resource_properties("AWS::Lambda::Function", {"MemorySize": 512})


def test_api_gateway_exists():
    template = Template.from_stack(make_stack())
    template.resource_count_is("AWS::ApiGatewayV2::Api", 1)


def test_api_gateway_route_slack_events():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {"RouteKey": "POST /slack/events"},
    )


def test_lambda_has_self_invoke_permission():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [Match.object_like({"Action": "lambda:InvokeFunction", "Effect": "Allow"})]
                )
            }
        },
    )


def test_lambda_has_agentcore_permission():
    template = Template.from_stack(make_stack())
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [Match.object_like({"Action": "bedrock-agentcore:InvokeAgentRuntime", "Effect": "Allow"})]
                )
            }
        },
    )


def test_cfn_output_endpoint_url():
    template = Template.from_stack(make_stack())
    template.has_output("SlackEndpointUrl", {})


def test_dev_uses_delete_policy():
    template = Template.from_stack(make_stack("dev"))
    template.has_resource(
        "AWS::Lambda::Function",
        {"DeletionPolicy": "Delete"},
    )


def test_prod_uses_retain_policy():
    template = Template.from_stack(make_stack("prod"))
    template.has_resource(
        "AWS::Lambda::Function",
        {"DeletionPolicy": "Retain"},
    )
