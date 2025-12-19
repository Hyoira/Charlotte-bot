import pandas as pd
import os



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
