# Operation Agent

障害診断エージェント - Strands Agents SDK + Amazon Bedrock

## 開発ワークフロー

1. **ユーザーがIssueを指定** して着手を指示する（Claudeが勝手にIssueを始めないこと）
2. **ブランチを切る**: `feature/<issue番号>-<短い説明>` or `fix/<issue番号>-<短い説明>`
3. **テストを先に書く**（TDD: Red → Green → Refactor）
4. **実装 & コミット**
5. **PRを作成**: 本文に `Closes #<issue番号>` を含める
6. **レビュー & マージ**

## 優先度ラベル

| ラベル | 色 | 意味 | 着手基準 |
|--------|-----|------|----------|
| `P0` | 赤 | 最優先: ブロッカー | 他をブロックしている。即着手 |
| `P1` | 黄 | 高: 次に着手 | P0完了後、依存が解消され次第着手 |
| `P2` | 緑 | 中: 余裕があれば | P1がおおむね完了してから着手 |

## 実装順序

```
P0: #1 初期セットアップ → #2 エージェントコア
P1: #3 カスタムツール, #4 Notion検索, #6 テスト, #9 CI（並行可）
P2: #7 AgentCoreデプロイ, #8 Slack Bot, #10 O11y, #11 IaC
```

## コマンド

```bash
uv sync --all-extras        # 依存関係インストール
uv run ruff check src/      # lint
uv run ruff format src/     # format
uv run pytest tests/        # テスト実行
uv run pytest tests/ -m integration  # 統合テスト（AWS認証必要）
```

## コーディング規約

- Python 3.10+
- Ruff準拠（設定は pyproject.toml）
- line-length: 120
- Lefthookでpre-commit時にlint/format自動チェック
- **TDD**: pytestでテストを先に書き、失敗を確認してから実装する

## プロジェクト構造

```
src/diagnosis/
├── agent.py      # create_agent() ファクトリ関数
├── config.py     # pydantic-settingsで環境変数管理（DIAG_プレフィックス）
├── prompts.py    # システムプロンプト
└── tools/        # @tool デコレータでカスタムツール定義
    ├── cwl_insights.py   # CloudWatch Logs Insightsでログ検索
    ├── mysql_query.py    # Lambda経由でMySQL参照
    └── notion_search.py  # Notionからドキュメント検索
```

## 環境変数（.env）

```
DIAG_AWS_REGION=us-west-2
DIAG_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
AWS_PROFILE=              # AWS CLIプロファイル
NOTION_API_KEY=           # Notion APIキー
```
