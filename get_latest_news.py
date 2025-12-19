from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
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

    @staticmethod
    def scrape_wait(url, selector):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--lang=ja-JP")
        options.add_experimental_option('prefs', {'intl.accept_languages': 'ja-JP'})

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)
            # Wait for specific element to load (dynamic loading)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            # Scroll down to ensure images lazy load if necessary, though scraper often gets src anyway.
            # But for infinite scroll items, we might need a scroll. 
            # For the first batch, just waiting is usually enough.
            # Adding a small scroll just in case
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(2)
            
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

    @staticmethod
    def convert_hoyolab(html):
        soup = BeautifulSoup(html, 'html.parser')
        data = []

        # Assuming the inspection found .mhy-article-card
        for news_item in soup.select('.mhy-article-card'):
            try:
                # URL
                link_tag = news_item.select_one('.mhy-article-card__link')
                if not link_tag:
                    continue
                url = f"https://www.hoyolab.com{link_tag['href']}"
                
                # Title
                title_tag = news_item.select_one('.mhy-article-card__title')
                title = title_tag.get_text(strip=True).replace('\n', '<n>') if title_tag else "No Title"

                # Cover Image
                # Some posts might not have images or use different structure
                img_tag = news_item.select_one('.mhy-article-card__img img')
                if img_tag and 'src' in img_tag.attrs:
                    src = img_tag['src']
                    if src.startswith('http'):
                        cover_image = src
                    else:
                        cover_image = ""
                else:
                    cover_image = "" # fallback/placeholder

                # Summary
                summary_tag = news_item.select_one('.mhy-article-card__content')
                summary = summary_tag.get_text(strip=True).replace('\n', '<n>') if summary_tag else ' '

                data.append({
                    "Title": title,
                    "URL": url,
                    "Cover Image": cover_image,
                    "Summary": summary
                })
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue
            
        return pd.DataFrame(data).fillna('')

class UpdateCheck: # データの比較
    @staticmethod
    def check_for_updates(old_file, new_data, merge_keys=None):
        if merge_keys is None:
            merge_keys = ["Title", "URL", "Cover Image", "Summary"]

        # 前回の取得情報を読み込む
        try:
            old_data = pd.read_csv(old_file).fillna('')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            print(f"First run detected: Initializing '{old_file}' without notifications.")
            new_data.to_csv(old_file, index=False)
            return pd.DataFrame()

        # 新しいカラム（ann_idなど）がold_dataにない場合のエラーを防ぐため、
        # old_dataにないカラムはマージキーから除外するか、あるいは無視する。
        # 単純化のため、merge_keysに含まれるカラムが両方のDFにあることを前提とするが、
        # GameNewsの場合はCSV保存時に全カラム保存されるので問題ないはず。
        
        # マージキーの型不一致を防ぐため、文字列に統一する
        for key in merge_keys:
            if key in new_data.columns:
                new_data[key] = new_data[key].astype(str)
            
            # old_dataにキーが存在しない場合は、比較不能なので全件新規扱いとする
            if key not in old_data.columns:
                print(f"Old data missing key '{key}'. Treating all as new.")
                return new_data
                
            old_data[key] = old_data[key].astype(str)

        # カラム衝突（_x, _y）を防ぐため、old_dataはマージキーのみを使用する
        merged_data = pd.merge(
            new_data,
            old_data[merge_keys],
            on=merge_keys, 
            how='left', 
            indicator=True)
        
        new_entries = merged_data[merged_data['_merge'] == 'left_only'] # 新規記事だけを抽出
        
        new_entries.drop(columns=['_merge']).to_csv('new_entries.csv', index=False) # テスト用

        if not new_entries.empty:
            # new_entries.to_csv(old_file, index=False)
            print(f"{len(new_entries)}件の新着記事があります")
        # else:
            # print("新着記事なし")

        return new_entries.drop(columns=['_merge']).fillna('')

class GameNews: # ゲーム内お知らせの取得
    @staticmethod
    def fetch_announcements():
        import urllib.request
        import json
        import re
        from datetime import datetime
        
        url = "https://sg-hk4e-api.hoyoverse.com/common/hk4e_global/announcement/api/getAnnList?game=hk4e&game_biz=hk4e_global&lang=ja&bundle_id=hk4e_global&platform=pc&region=os_asia&level=55&uid=888888888&auth_appid=announcement"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                
            if data['retcode'] != 0:
                print(f"API Error: {data['message']}")
                return pd.DataFrame()

            announcements = []
            # APIのレスポンス構造: data -> list -> list (各カテゴリ) -> list (記事)
            for category in data['data']['list']:
                for item in category['list']:
                    # 必要な情報を抽出
                    title = item.get('title', '')
                    
                    # HTMLタグの除去と改行の置換
                    raw_subtitle = item.get('subtitle', '')
                    # <br>, <br/>, <br /> 等をスペースに置換
                    subtitle = re.sub(r'<br\s*/?>', ' ', raw_subtitle, flags=re.IGNORECASE)
                    # その他のHTMLタグを除去
                    subtitle = re.sub(r'<[^>]+>', '', subtitle)
                    # 改行コードの削除
                    subtitle = subtitle.replace('\r', '').replace('\n', ' ')
                    
                    banner = item.get('banner', '')
                    ann_id = str(item.get('ann_id'))
                    
                    start_time_str = item.get('start_time', '')
                    end_time_str = item.get('end_time', '')
                    
                    start_timestamp = 0
                    end_timestamp = 0
                    
                    try:
                        if start_time_str:
                            dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                            start_timestamp = int(dt.timestamp())
                        if end_time_str:
                            dt = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                            end_timestamp = int(dt.timestamp())
                    except ValueError:
                        pass
                    
                    # URLはゲーム内用のため、Webで閲覧可能な形式がない場合は空文字または仮のURLとする
                    # ここでは一旦空文字にする (Discordでリンクなしになる)
                    # またはIDを使って将来的に詳細取得機能を作ることも可能
                    url = "" 
                    
                    announcements.append({
                        "Title": title,
                        "URL": url, # 仮
                        "Cover Image": banner,
                        "Summary": subtitle,
                        "ann_id": ann_id,
                        "start_time": start_time_str,
                        "end_time": end_time_str,
                        "start_timestamp": start_timestamp,
                        "end_timestamp": end_timestamp
                    })
            
            df = pd.DataFrame(announcements)
            if not df.empty and 'start_time' in df.columns:
                df = df.sort_values(by='start_time', ascending=False)
            
            return df.fillna('')
            
        except Exception as e:
            print(f"Game Announcements Fetch Error: {e}")
            return pd.DataFrame()

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

    print("-" * 30)
    print("Testing HoYoLAB Fetch...")
    url_hoyolab = "https://www.hoyolab.com/accountCenter/postList?id=1015537"
    html_hoyolab = Scrape.scrape_wait(url_hoyolab, ".mhy-article-card")
    data_hoyolab = Convert.convert_hoyolab(html_hoyolab)
    
    checker_hoyolab = UpdateCheck()
    updates_hoyolab = checker_hoyolab.check_for_updates(os.path.abspath('hoyolab_data.csv'), data_hoyolab)

    if not updates_hoyolab.empty:
        print(f"HoYoLAB Updates Found: {len(updates_hoyolab)}")
        print(updates_hoyolab["Title"])
    else:
        print("No HoYoLAB updates.")
    
    data_hoyolab.to_csv(os.path.abspath('hoyolab_data.csv'), index=False)

    print("-" * 30)
    print("Testing Game Announcements Fetch...")
    game_news = GameNews.fetch_announcements()
    if not game_news.empty:
        print(f"Game Announcements Found: {len(game_news)}")
        print(game_news[["Title", "Summary"]].head())
        
        # Save to CSV for inspection
        csv_path = os.path.abspath('game_announcements.csv')
        
        # Check for updates
        print("Checking for game announcement updates...")
        updates_game = UpdateCheck.check_for_updates(csv_path, game_news, merge_keys=["ann_id"])
        if updates_game is not None and not updates_game.empty:
            print("Game Announcement Updates Found:")
            print(updates_game["Title"])
        else:
            print("No game announcement updates.")
            
        game_news.to_csv(csv_path, index=False)
        print(f"Saved game announcements to: {csv_path}")
    else:
        print("No game announcements found.")
