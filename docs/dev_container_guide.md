# Dev Container 利用ガイド

このプロジェクトは **Dev Container (Development Container)** に対応しています。
ローカルマシンの環境を汚すことなく、プロジェクト専用の隔離された開発環境（Dockerコンテナ）でBotを開発・実行できます。
「venvの切り替えが面倒」「Pythonのバージョン管理が大変」といった悩みから解放されます。

## メリット
- **環境構築が自動**: コンテナ起動時に `requirements.txt` のライブラリが自動インストールされます。
- **環境の統一**: チーム開発や別マシンへの移行時も、Dockerさえあれば同じ環境が再現されます。
- **VS Codeとの統合**: 普段と同じVS Codeの操作感で、コンテナ内のファイルを編集・デバッグできます。

## 事前準備
以下のソフトウェアをインストールしてください。

1. **Docker Desktop** (または [OrbStack](https://orbstack.dev/) ※macOS推奨)
   - コンテナを動かすためのエンジンです。
2. **Visual Studio Code**
3. **[Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)** (VS Code拡張機能)
   - その名の通り、Dev Containerを使うための拡張機能です。

## 使い方

### 1. プロジェクトを開く
VS Codeで `Charlotte-bot` フォルダを開きます。

### 2. コンテナで再度開く
ウィンドウ右下に「Reopen in Container」という通知が出る場合は、それをクリックします。
通知が出ない場合は、左下の緑色のアイコン（リモートインジケーター）をクリックし、コマンドパレットから **「Dev Containers: Reopen in Container」** を選択します。

### 3. 初回ビルド（待ち時間）
初回はDockerイメージのダウンロードとビルド、ライブラリのインストールが行われるため、数分かかります。
ターミナルにログが表示されるので、終わるまで待ちます。

### 4. 開発・実行
準備が完了すると、左下の緑色のアイコンが **「Dev Container: Charlotte-bot Dev」** に変わります。
この状態で開いているターミナルは、すでにコンテナ内部（仮想環境）です。

**Botの起動:**
```bash
python charlotte.py
```
> **Note**: `venv` を有効化するコマンド (`source venv/bin/activate`) は不要です。コンテナ全体が専用環境です。
> **Timezone**: コンテナ内のシステム時刻は通常 UTC ですが、Bot プログラム内で日本時間 (JST) を指定しているため、リマインダー等は日本時間で動作します。

### 5. 終了方法
VS Codeを閉じるか、左下の緑色のアイコンをクリックして **「Close Remote Connection」** を選択します。

## 注意事項 (Seleniumについて)
現在のDev Container設定は、Pythonスクリプト (`GameNews` 機能など) の実行に最適化されています。
もし `Selenium` (Chromeブラウザ操作) を使用する機能 (`get_latest_news.py` のスクレイピング機能の一部) を有効化したい場合は、コンテナ内にGoogle Chromeをインストールする必要がありますが、現在の軽量設定には含まれていません。
「ゲーム内お知らせ通知」機能のみを使用する場合は、現在の設定で問題ありません。
