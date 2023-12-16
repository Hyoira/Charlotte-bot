import pandas as pd
from bs4 import BeautifulSoup
import scraper
import os

class Comparator:
    
    def __init__(self):
        # スクレイピング処理を実行
        if __name__ == '__main__':
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
        self.articles = pd.DataFrame(data)
        print(data)

        # 前回のデータが保存されたCSVを読み込む / ない場合はリセット
        self.reset_or_load_previous_data()

        self.compare_and_export_data()
        
    def reset_or_load_previous_data(self):
        try:
            # Check if file is empty
            if os.path.getsize('entries_prev.csv') > 0:
                self.articles_prev = pd.read_csv('entries_prev.csv')
            else:
                raise ValueError("CSV file is empty.")
        except (FileNotFoundError, pd.errors.ParserError, ValueError) as e:
            print(f'Error with the CSV file: {e}. Resetting the file.')
            columns = ["Title", "URL", "Cover Image", "Summary"]
            self.articles_prev = pd.DataFrame(columns=columns)
            self.articles_prev.to_csv('entries_prev.csv', index=False)


    def compare_and_export_data(self):
        # 前回のデータが不足している場合のNaNを空文字に置換
        articles_prev_filled = self.articles_prev.fillna('')

        # 新しいデータと前回のデータフレームを比較して差分を抽出
        if not self.articles_prev.empty:
            # 新旧データフレームを結合し重複を取り除く
            articles_combined = pd.concat([articles_prev_filled, self.articles]).drop_duplicates(keep=False)

            # 差分データのみを抽出
            self.entries_new = articles_combined[~articles_combined.apply(tuple,1).isin(articles_prev_filled.apply(tuple,1))]
        else:
            # 前回のデータが存在しない場合は、すべてが新しいデータ
            self.entries_new = self.articles

        # 新しいデータをCSVファイルに書き出す
        self.articles.to_csv('entries_prev.csv', index=False, encoding='utf-8')

        # 差分データを別ファイルに書き出す
        self.entries_new.to_csv('entries_new.csv', index=False, encoding='utf-8')