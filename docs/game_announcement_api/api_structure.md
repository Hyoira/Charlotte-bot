# 原神 ゲーム内お知らせAPI (JSON) 仕様

## 概要
ゲーム内のお知らせ画面で使用されているAPIのエンドポイントと、レスポンスデータの構造についてまとめたドキュメントです。
本APIを使用することで、公式Webサイトよりも早く、かつゲーム内と同じお知らせ情報を取得することが可能です。

## エンドポイント
`GET https://sg-hk4e-api.hoyoverse.com/common/hk4e_global/announcement/api/getAnnList`

### 主な必須パラメータ
これらはURLクエリパラメータとして付与します。

- `game`: `hk4e` (原神を表すコード)
- `game_biz`: `hk4e_global` (グローバル版)
- `lang`: `ja` (日本語)
- `bundle_id`: `hk4e_global`
- `auth_appid`: `announcement`

### その他のパラメータ (任意または状況依存)
- `platform`: `pc` (pc, android, ios など)
- `region`: `os_asia` (サーバーリージョン。os_asia, os_usa, os_euro, os_cht など)
- `level`: ユーザーレベル (特定のレベル帯向けのお知らせフィルタリング用)
- `uid`: ユーザーID

## レスポンス構造 (JSON)

ルートオブジェクト:
```json
{
  "retcode": 0,       // レスポンスコード (0: 正常)
  "message": "OK",    // ステータスメッセージ
  "data": { ... }     // データ本体を含むオブジェクト
}
```

### `data` オブジェクト
| フィールド | 型 | 説明 |
| --- | --- | --- |
| `list` | Array | **お知らせカテゴリのリスト**。APIレスポンスの本体で、「イベント」「重要」などの各タブごとに記事リストが格納されています。 |
| `total` | Int | 取得できたお知らせの総数 |
| `type_list` | Array | カテゴリ定義情報のリスト (`id`, `name`, `mi18n_name`) |
| `timezone` | Int | サーバータイムゾーン (例: 8) |
| `t` | String | キャッシュ無効化あるいはタイムスタンプ用の値 |

### `data.list` (カテゴリ) の構造
`data.list` 配下の各要素は、1つのカテゴリ（タブ）と、それに属する記事リストを表します。

| フィールド | 型 | 説明 |
| --- | --- | --- |
| `list` | Array | そのカテゴリに属する **お知らせ記事のリスト** |
| `type_id` | Int | カテゴリID (例: 2:重要, 1:イベント) |
| `type_label` | String | カテゴリ名 (例: "イベント", "重要") |

### `data.list[].list` (お知らせ記事) の構造
最も重要な記事データの構造です。ここに個々のお知らせ情報が含まれます。

```json
{
    "ann_id": 21495,
    "title": "「Luna Ⅲ」最新情報一覧",
    "subtitle": "「Luna Ⅲ」最新情報一覧",
    "banner": "https://sdk.hoyoverse.com/upload/ann/.../example.jpg",
    "content": "...",
    "lang": "ja-jp",
    "start_time": "2025-12-03 07:00:00",
    "end_time": "2026-01-14 06:00:00",
    "type_label": "重要",
    "tag_label": "3",
    "login_alert": 1,
    "remind": 1,
    "alert": 0,
    "has_content": true
}
```

| フィールド | 型 | 説明 |
| --- | --- | --- |
| `ann_id` | Int | **記事ID**。一意の識別子。更新検知にはこのIDを使用することを推奨します。 |
| `title` | String | お知らせのタイトル。 |
| `subtitle` | String | お知らせの概要（サブタイトル）。一覧表示用。**注意**: 改行コード (`\r`, `\n`) が含まれる場合があるため、CSV保存時などは置換処理が必要です。 |
| `banner` | String | バナー画像のURL。画像がない場合は空文字の場合があります。 |
| `content` | String | 記事の本文HTML。空の場合もある（Webビューで別URLを開くタイプなど）。実装によってはここから詳細情報をパース可能。 |
| `start_time` | String | 掲載開始日時 (YYYY-MM-DD HH:MM:SS)。新しい順にソートする際に使用します。 |
| `end_time` | String | 掲載終了日時。 |
| `type_label` | String | ラベル表示用テキスト (例: "重要")。 |
| `tag_icon` | String | タグアイコンのURL。 |

## データ取得・使用時の注意点
1. **API利用制限**: あくまで内部APIであるため、過度なリクエストは避け、常識的な範囲（例えば数分〜数十分に1回など）でポーリングしてください。
2. **日時ソート**: APIからのレスポンスは必ずしも日付順とは限らないため、`start_time` を使用して降順ソートすることで「最新のお知らせ」として扱いやすくなります。
3. **データ保存**: CSV等に保存する際、`subtitle` や `content` に含まれる特殊文字や改行コードによるフォーマット崩れに注意が必要です。

## 本文取得用API (`getAnnContent`)
一覧取得API (`getAnnList`) では `content` フィールドが空の場合があります。
詳細なHTML本文を取得するには、別途以下のエンドポイントを使用します。

### エンドポイント
`GET https://sg-hk4e-api.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent`

パラメータは `getAnnList` と同様です。

### レスポンス構造
`data.list` 内の各オブジェクトに、`ann_id` と対になる形で `content` (HTML文字列) が格納されています。
`getAnnList` で取得したリストと `ann_id` をキーにしてマージすることで、タイトルや期間情報と本文を紐付けることが可能です。
