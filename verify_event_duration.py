from get_latest_news import GameNews
from bs4 import BeautifulSoup
import re
import pandas as pd

def verify_extraction():
    print("Fetching announcements...")
    df = GameNews.fetch_announcements()
    
    if df.empty:
        print("No announcements found.")
        return

    print(f"Fetched {len(df)} announcements.")
    
    # Regex pattern to find Duration headers
    # Common headers: 〓イベント期間〓, 〓祈願期間〓, 〓販売期間〓
    duration_pattern = re.compile(r'〓(.*?)期間〓')
    
    count_success = 0
    
    for index, row in df.iterrows():
        title = row['Title']
        content_html = row.get('content', '')
        
        if not content_html:
            continue
            
        soup = BeautifulSoup(content_html, 'html.parser')
        text = soup.get_text(separator='\n')
        
        # Find the header
        match = duration_pattern.search(text)
        if match:
            print(f"\n[FOUND] {title}")
            print(f"Header: {match.group(0)}")
            
            # Identify the text block following the header
            # Simple approach: split by header and take the start of the next part
            parts = text.split(match.group(0))
            if len(parts) > 1:
                # Get the immediate next few lines
                after_header = parts[1].strip()
                # Take lines until the next "〓" or end
                duration_text_lines = []
                for line in after_header.split('\n'):
                    line = line.strip()
                    if not line: continue
                    if line.startswith('〓'): break
                    duration_text_lines.append(line)
                    # Limit to e.g. 5 lines to avoid printing entire body
                    if len(duration_text_lines) >= 3: break
                
                print(f"Extracted Text: {' / '.join(duration_text_lines)}")
                count_success += 1
        else:
            # print(f"[SKIP] {title} (No duration header found)")
            pass
            
    print(f"\nTotal items with duration found: {count_success} / {len(df)}")

if __name__ == "__main__":
    verify_extraction()
