from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import os

class Scrape: # データの取得
    @staticmethod
    def scrape(url):
        options = Options()
        options.add_argument("--headless") # ヘッドレスモードを有効化
        options.add_argument("--lang=ja-JP") # 日本語ページを指定
        options.add_experimental_option('prefs', {'intl.accept_languages': 'ja-JP'})

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)
            html = driver.page_source
            return html
        finally:
            driver.quit()

class Convert: # データの整形
    @staticmethod
    def convert(html):
        soup = BeautifulSoup(html, 'html.parser') # BeautifulSoupのオブジェクトを作成
        data = []

        # 記事のタイトル、URL、サムネイル画像、概要を取得
        for news_item in soup.find_all('a', class_='news__title news__content ellipsis'):
            url = f"https://genshin.hoyoverse.com{news_item['href']}"
            title = news_item.find('h3').get_text(strip=True).replace('\n', '<n>')
            cover_image = news_item.find('img', class_='coverFit')['src']

            if news_item.find('p', class_='news__summary').get_text(strip=True) == '':
                print(f"概要がありません: {title} ({url})")
                summary = ' '
            else:
                summary = news_item.find('p', class_='news__summary').get_text(strip=True).replace('\n', '<n>')

            data.append({
                "Title": title,
                "URL": url,
                "Cover Image": cover_image,
                "Summary": summary
            })

        return pd.DataFrame(data).fillna('') # データフレームに変換

class UpdateCheck: # データの比較
    @staticmethod
    def check_for_updates(old_file, new_data):
        # 前回の取得情報を読み込む
        try:
            old_data = pd.read_csv(old_file)
        except FileNotFoundError:
            print(f"'{old_file}'に前回の取得情報がありません。")
            return new_data

        merged_data = pd.merge(
            new_data,
            old_data,
            on=["Title", "URL", "Cover Image", "Summary"], 
            how='left', 
            indicator=True)
        
        new_entries = merged_data[merged_data['_merge'] == 'left_only'] # 新規記事だけを抽出
        
        new_entries.drop(columns=['_merge']).to_csv('new_entries.csv', index=False) # テスト用

        if not new_entries.empty:
            # new_entries.to_csv(old_file, index=False)
            print(f"{len(new_entries)}件の新着記事があります")
        # else:
            # print("新着記事なし")

        return new_entries.drop(columns=['_merge'])

# テスト用
if __name__ == "__main__":
    url = "https://genshin.hoyoverse.com/ja/news/"
    html = Scrape.scrape(url)
    new_data = Convert.convert(html)

    checker = UpdateCheck()
    updates = checker.check_for_updates(os.path.abspath('data_prev.csv'), new_data)

    if not updates.empty:
        print(updates["Title"])
    else:
        print("新着記事なし")

    new_data.to_csv(os.path.abspath('data_prev.csv'), index=False)
