from diagnosis.agent import create_agent

agent = create_agent()
response = agent("本番環境でDBへの接続が急増しています。原因を調査してください。")
print(response)
