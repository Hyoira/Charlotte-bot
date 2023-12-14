from selenium import webdriver
from bs4 import BeautifulSoup
import chromedriver_binary

class Scraper:
  # WebDriverのパスとオプションを設定
  driver = webdriver.Chrome()

  # スクレイピングするページのURL
  url = "https://genshin.hoyoverse.com/ja/news/"

  # JavaScriptが実行されるまで待つためにページを取得
  driver.get(url)

  # JavaScriptによりレンダリングされたHTMLを取得
  html = driver.page_source

  # BeautifulSoupでパース
  soup = BeautifulSoup(html, 'html.parser')

  # 取得したページをファイルに保存
  # with open("response02.html", mode="w", encoding="utf-8") as f:
  #     f.write(soup.prettify())

  titles = soup.select(".news__content")
  infos = soup.select(".news__info")
  discriptions = soup.select(".news__summary")

  # 文字列に変換してファイルに書き込む
  with open('response02_scraped.html', 'w', encoding='utf-8') as file:
      for link in titles:
          file.write(str(link) + '\n')  # 各リンクのHTMLを文字列として書き込む

  # WebDriverを閉じます
  driver.quit()