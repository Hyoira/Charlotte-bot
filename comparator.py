import pandas as pd
from bs4 import BeautifulSoup
import scraper


class Comparator:

  # スクレイピング処理を実行
  scraper.Scraper() 

  # パース済みhtmlファイル
  file_path = './scraped.html'

  # データを格納するための空のリストを作成
  data = []

  # ファイルを読み込み、BeautifulSoupオブジェクトを作成
  with open(file_path, 'r', encoding='utf-8') as file:
      soup = BeautifulSoup(file, 'html.parser')


  for news_item in soup.find_all('a', class_='news__title'):
      # 各項目から必要な情報を取得
      url = f"https://genshin.hoyoverse.com{news_item['href']}"
      title = news_item.find('h3').get_text(strip=True)
      cover_image = news_item.find('img', class_='coverFit')['src']
      summary = news_item.find('p', class_='news__summary').get_text(strip=True)
      
      # データをリストに追加
      data.append({
          "Title": title,
          "URL": url,
          "Cover Image": cover_image,
          "Summary": summary
      })

  # データリストからPandasデータフレームを作成
  articles = pd.DataFrame(data)

  # 前回のデータが保存されたCSVを読み込む
  # 前回のデータがない場合は空のDataFrameを作成する
  try:
      articles_prev = pd.read_csv('entries_prev.csv')
  except FileNotFoundError:
      articles_prev = pd.DataFrame(columns=["Title", "URL", "Cover Image", "Summary"])

  articles_prev_filled = articles_prev.fillna('')

  # 新しいデータと前回のデータフレームを比較して差分を抽出
  if not articles_prev.empty:
      # 新旧データフレームの結合と重複の削除
      articles_combined = pd.concat([articles_prev_filled, articles]).drop_duplicates(keep=False)
      
      # 差分データのみを抽出
      entries_new = articles_combined[~articles_combined.apply(tuple,1).isin(articles_prev_filled.apply(tuple,1))]
  else:
      # 前回のデータが存在しない場合は、新しいデータすべてが差分
      entries_new = articles


  # 新しいデータをCSVファイルに書き出す（次回比較用）
  articles.to_csv('entries_prev.csv', index=False, encoding='utf-8')

  # 差分データを別のCSVファイルで管理する場合（オプション）
  entries_new.to_csv('entries_new.csv', index=False, encoding='utf-8')