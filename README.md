# slack-stats

Slack での自分の発言数・参加チャンネル数・発言傾向などを調べる CLI ツールです。

- 発言数(全体 / 期間指定 / チャンネル別)
- 参加チャンネル数(パブリック / プライベート / DM / グループDM の内訳)
- 発言数の多いチャンネル ランキング(任意)
- 曜日別・時間帯別の発言傾向(バーチャート表示)

内部的には Slack の検索 API (`search.messages`) と会話一覧 API
(`users.conversations`) を呼び出して集計しています。メッセージ本文の取得は
行わないため、比較的高速に動作します。

## セットアップ

### 1. Slack App の作成とトークン取得

発言数の集計に Slack の検索 API (`search.messages`) を使用するため、**User
OAuth Token** (`xoxp-` から始まるトークン) が必要です。Bot トークンでは検索
API は利用できません。

1. https://api.slack.com/apps で新しい App を作成(対象ワークスペースを選択)
2. "OAuth & Permissions" ページで **User Token Scopes** に以下を追加

   | スコープ | 用途 |
   | --- | --- |
   | `search:read` | 発言数・発言傾向の集計 (`search.messages`) |
   | `channels:read` | 参加パブリックチャンネルの取得 |
   | `groups:read` | 参加プライベートチャンネルの取得 |
   | `mpim:read` | 参加グループDMの取得 |
   | `im:read` | 参加DMの取得 |

3. ワークスペースに App をインストールし、発行された `xoxp-...` トークンを控える

### 2. インストール

```bash
pip install -e .
```

開発用の依存関係(pytest)も含めてインストールする場合:

```bash
pip install -e ".[dev]"
```

### 3. トークンの設定

```bash
cp .env.example .env
# .env を編集して SLACK_USER_TOKEN=xoxp-... を設定
```

環境変数 `SLACK_USER_TOKEN` を直接設定してもかまいません(`.env` は
[python-dotenv](https://pypi.org/project/python-dotenv/) により自動で読み込まれます)。

### 4. 動作確認

```bash
slack-stats whoami
```

トークンに紐づくユーザー名・チーム名が表示されれば設定完了です。

## コマンド一覧

各コマンドの詳細は `slack-stats <コマンド> --help` でも確認できます。

| コマンド | 説明 |
| --- | --- |
| `whoami` | トークンに紐づくユーザー・ワークスペース情報を表示 |
| `channels` | 参加チャンネル数を種別ごとに表示 |
| `messages` | 発言数を表示(期間指定可) |
| `summary` | チャンネル数・発言数をまとめて表示(上位チャンネルの表示も可) |
| `activity` | 曜日別・時間帯別の発言傾向をバーチャートで表示 |

### `whoami`

```bash
slack-stats whoami
```

設定した `SLACK_USER_TOKEN` が正しいか、意図したワークスペースに
紐づいているかを確認する疎通確認用コマンドです。

### `channels`

```bash
slack-stats channels
```

自分が参加しているパブリックチャンネル・プライベートチャンネル・DM・
グループDM の件数を種別ごとに表示します。

### `messages`

```bash
# 全期間の発言数
slack-stats messages

# 期間を指定して発言数を表示(--since は指定日を含まない)
slack-stats messages --since 2026-01-01 --until 2026-07-01
```

| オプション | 説明 |
| --- | --- |
| `--since YYYY-MM-DD` | この日付以降を集計(指定日を含まない) |
| `--until YYYY-MM-DD` | この日付以前を集計(指定日を含まない) |

### `summary`

```bash
# 発言数・参加チャンネル数をまとめて表示
slack-stats summary

# 発言数の多いチャンネル上位5件も合わせて表示
# (チャンネル数だけ検索APIを呼ぶため、チャンネル数が多いと時間がかかります)
slack-stats summary --since 2026-01-01 --top 5
```

| オプション | 説明 |
| --- | --- |
| `--since YYYY-MM-DD` | この日付以降を集計 |
| `--until YYYY-MM-DD` | この日付以前を集計 |
| `--top N` | 発言数の多いチャンネルを上位N件表示(既定は0=無効) |

### `activity`

```bash
# 直近1000件を対象に曜日別・時間帯別の発言傾向を表示
slack-stats activity

# 集計対象の件数や期間を指定(0で全件取得)
slack-stats activity --since 2026-01-01 --max-messages 0
```

| オプション | 説明 |
| --- | --- |
| `--since YYYY-MM-DD` | この日付以降を集計 |
| `--until YYYY-MM-DD` | この日付以前を集計 |
| `--max-messages N` | 集計に使う最大メッセージ数(既定1000件、0で全件) |

曜日・時間帯は**実行環境のローカルタイムゾーン**で判定されます。異なる
タイムゾーンで集計したい場合は `TZ` 環境変数を設定して実行してください
(例: `TZ=Asia/Tokyo slack-stats activity`)。

## 開発

```bash
pip install -e ".[dev]"
pytest
```

`src/slack_stats/formatting.py` の集計・整形ロジックは Slack API に依存しない
純粋関数として実装されており、`tests/test_formatting.py` でユニットテスト
しています。

## 注意事項・トラブルシューティング

- `search.messages` は Slack のレート制限が厳しめです。`summary --top` や
  `activity` コマンド使用時、大規模ワークスペースでは実行に時間がかかる
  場合があります(429 が返った場合は `Retry-After` を尊重して自動リトライ
  します)。
- `after:` / `before:` は指定日を**含まない**検索になります(Slack 検索構文
  の仕様)。
- `SLACK_USER_TOKEN が設定されていません` と表示される場合は、`.env` の作成
  漏れ、もしくは環境変数名の誤りが考えられます。
- `not_allowed_token_type` などのエラーが出る場合、Bot トークン
  (`xoxb-...`) を設定していないか確認してください。本ツールは User トークン
  (`xoxp-...`) のみ対応しています。
- `missing_scope` エラーが出る場合、上記の User Token Scopes が過不足なく
  設定・再インストールされているか確認してください。
