from selenium import webdriver
from bs4 import BeautifulSoup
import chromedriver_binary
from selenium.webdriver.chrome.options import Options

class Scraper:
  # WebDriverのパスとオプションを設定
  options = Options()
  options.add_argument("--no-sandbox")  # サンドボックスモードを無効化するオプション
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