"""AWS Lambda エントリポイント。"""

from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from slack_bot.app import app

slack_handler = SlackRequestHandler(app=app)


def handler(event: dict, context: object) -> dict:
    return slack_handler.handle(event, context)
