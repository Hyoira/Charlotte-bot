from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import os

class Scrape:
  # WebDriverのパスとオプションを設定
  options = Options()
  options.add_argument("--no-sandbox")  # サンドボックスモードを無効化するオプション
  options.add_argument("--headless")  # ヘッドレスモードを有効化するオプション
  options.add_experimental_option('prefs', {'intl.accept_languages': 'ja'}) # 言語を日本語に設定するオプション
  driver = webdriver.Chrome(options=options)

    # スクレイピング対象のURL
  url = "https://genshin.hoyoverse.com/ja/news/"

  # JavaScriptが実行されるまで待つためにページを取得
  driver.get(url)

  # JavaScriptによりレンダリングされたHTMLを取得
  html = driver.page_source

  # BeautifulSoupでパース
  soup = BeautifulSoup(html, 'html.parser')

  titles = soup.select(".news__content")
  infos = soup.select(".news__info")
  discriptions = soup.select(".news__summary")

  # 文字列に変換してファイルに書き込む
  with open('scraped.html', 'w', encoding='utf-8') as file:
      for link in titles:
          file.write(str(link) + '\n')  # 各リンクのHTMLを文字列として書き込む

  # WebDriverを閉じます
  driver.quit()

  print("Scraped")


class Convert:
  # パース済みhtmlファイル
  file_path = './scraped.html'

  # データを格納するための空のリストを作成
  data = []

  # ファイルを読み込み、BeautifulSoupオブジェクトを作成
  with open(file_path, 'r', encoding='utf-8') as file:
      soup = BeautifulSoup(file, 'html.parser')

  for news_item in soup.find_all('a', class_='news__title news__content ellipsis'):
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

  print("Converted")


class UpdateCheck:
    @staticmethod
    def check_for_updates(old_file, new_data):
        # 以前のデータを読み込む
        try:
            old_data = pd.read_csv(old_file)
        except FileNotFoundError:
            print(f"No previous data file found at '{old_file}'. Assuming all data is new.")
            return new_data

        # 新しいデータフレームと古いデータフレームを比較し、更新を確認
        merged_data = pd.merge(new_data, old_data, on=["Title", "URL", "Cover Image", "Summary"], 
                               how='left', indicator=True)
        new_entries = merged_data[merged_data['_merge'] == 'left_only']

        # 新しいデータをCSVに書き込む
        if not new_entries.empty:
            new_entries.to_csv(old_file, index=False)
            print(f"Found {len(new_entries)} new entries.")
        else:
            print("No new entries found.")

        return new_entries.drop(columns=['_merge'])
    
    print("Update Checked")


if __name__ == "__main__":
    new_data = Convert.articles
    checker = UpdateCheck()

    # 新しい更新がある行のみを取得
    updates = checker.check_for_updates('data_prev.csv', new_data)
    
    if not updates.empty:
      print(updates["Title"])
    else:
      print("No updates")

    # 新しいデータをCSVファイルに保存、次回更新チェック用
    new_data.to_csv('data_prev.csv', index=False)