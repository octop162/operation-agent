# Operation Agent

障害診断エージェント - Strands Agents SDK + Amazon Bedrock

## ワークフロー

1. **ユーザーがIssueを指定して着手を指示する**（勝手にIssueを始めない）
2. ブランチ: `feature/<issue番号>-<短い説明>` or `fix/<issue番号>-<短い説明>`
3. **TDD**: テストを先に書き、失敗確認してから実装（Red → Green → Refactor）
4. PR本文に `Closes #<issue番号>` を含める

## コマンド

```bash
uv sync --all-extras                  # 依存インストール
uv run ruff check src/                # lint
uv run ruff format src/               # format
uv run pytest tests/                  # テスト
uv run pytest tests/ -m integration   # 統合テスト（AWS認証必要）
```

## ルール

- Python 3.10+ / Ruff準拠（設定は pyproject.toml）
- Conventional Commits: `feat:` `fix:` `docs:` `refactor:` `test:` `chore:`
- .envファイルは絶対に編集・コミットしない
- リンター設定（pyproject.toml, lefthook.yml）を変更しない — コードを直す
- `--no-verify` 禁止 — フック失敗時は原因を修正する
- Hookによる保護ファイルの変更が必要な場合は、自分で編集せずユーザーに理由と変更内容を伝えて確認を取る

## 実装順序

```
P0: #1 初期セットアップ → #2 エージェントコア
P1: #3 カスタムツール, #4 Notion検索, #6 テスト, #9 CI（並行可）
P2: #7 AgentCoreデプロイ, #8 Slack Bot, #10 O11y, #11 IaC
```

## ハーネス

品質はHooksで機械的に強制される（`.claude/settings.json`参照）:
- **PostToolUse**: Pythonファイル編集 → Ruff自動修正+フォーマット → mypy型チェック
- **PreToolUse**: 設定ファイル保護 / 破壊的コマンドブロック / .env保護
- **Stop**: pytest全パスまで完了させない
- **Pre-commit**: Lefthookでlint/format/型チェック
