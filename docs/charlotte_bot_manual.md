# Charlotte-bot 取扱説明書

## 概要
Charlotte-bot (しゃるぼ) は、Discordサーバーに原神の最新情報やゲーム内お知らせを自動通知するためのBotです。
HoYoLABの記事や公式サイトのニュース、ゲーム内のお知らせAPIなど複数のソースから情報を収集し、DiscordチャンネルにEmbed形式で投稿します。

## 主な機能

1. **ゲーム内お知らせ自動通知** (現在稼働中)
   - ゲーム内API (`sg-hk4e-api.hoyoverse.com`) から最新のお知らせを取得します。
   - 新着記事を検知すると、指定したDiscordチャンネルに即座に通知します。
   - 通知には記事のタイトル、概要、バナー画像、イベント期間（Unix Timestamp形式）が含まれます。
   - お知らせデータは `game_announcements.csv` にバックアップ保存されます。

2. **[無効化中] 公式サイトニュース通知**
   - 原神公式サイト (`genshin.hoyoverse.com`) のニュースを取得します。
   - *現在は設定により停止中ですが、必要に応じて有効化可能です。*

3. **[無効化中] HoYoLAB記事通知**
   - HoYoLABの公式アカウントから投稿された記事を取得します。
   - *現在は設定により停止中ですが、必要に応じて有効化可能です。*

4. **リマインダー機能** 
   - 螺旋更新日やエスコフィエの通知機能など。
   - リマインダーは **日本時間 (JST / UTC+9)** に基づいて動作します。

## 導入・設定方法

### 必要要件
- Python 3.9 以上
- Google Chrome (Seleniumを使用したスクレイピング用 ※HoYoLAB/公式サイト機能使用時)
- Chrome Driver (同上)

### インストール手順
1. リポジトリをクローンします。
2. 依存ライブラリをインストールします。
   ```bash
   pip install -r requirements.txt
   ```
   > **注意**: `discord.py`, `selenium`, `beautifulsoup4`, `pandas` などが必要です。

### 開発環境 (Dev Container)
本プロジェクトは **Dev Container** に対応しており、Docker環境があれば `venv` の設定不要で開発を始められます。
詳しくは [Dev Container 利用ガイド](dev_container_guide.md) を参照してください。

### 環境変数の設定
プロジェクトルートに `.env` ファイルを作成し、以下の変数を設定してください。

```ini
BOT_TOKEN=あなたのDiscord_Bot_Token
CHANNEL_IDS=通知先チャンネルID1, 通知先チャンネルID2
# GUILD_IDS=... (スラッシュコマンド同期用のギルドID、任意)
```

## フォルダ構成
- `charlotte.py`: Botのメインスクリプト。起動・タスク管理を行います。
- `get_latest_news.py`: ニュース取得・スクレイピングロジック・更新検知ロジックを含むモジュールです。
- `requirements.txt`: 依存ライブラリ一覧。
- `docs/`: ドキュメントフォルダ。
- `game_announcements.csv`: ゲーム内お知らせのデータ保管ファイル。

## 使用方法

### Botの起動
```bash
python charlotte.py
```
起動すると、30分ごとに自動的にお知らせをチェックし、更新があれば通知します。

> [!NOTE]
> 初回起動時（`.csv` ファイルが存在しない場合）は、**既存のお知らせの通知を行わず、データを保存するのみ**となります。2回目以降のチェックから、新着判定が行われます。

### ゲーム内お知らせのデータ構造
取得したデータは `game_announcements.csv` に以下のカラムで保存されます。
- `Title`: お知らせタイトル
- `URL`: 記事URL (現在はAPI仕様上空文字の場合が多い)
- `Cover Image`: バナー画像URL
- `Summary`: 記事概要 (HTMLタグ除去・整形済み)
- `ann_id`: 記事固有ID
- `start_time`, `end_time`: 開始・終了日時
- `start_timestamp`, `end_timestamp`: Unix Timestamp (Bot通知用)

## トラブルシューティング
- **Botが起動しない**: `.env` ファイルの `BOT_TOKEN` が正しいか確認してください。
- **通知が来ない**: `CHANNEL_IDS` に正しいチャンネルIDが設定されているか、Botにそのチャンネルへの投稿権限があるか確認してください。
- **ImportError**: 必要なライブラリがインストールされていない可能性があります。 `pip install -r requirements.txt` を再実行してください。
