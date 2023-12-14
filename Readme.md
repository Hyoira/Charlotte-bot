## 必要なパッケージのインストール
### pyenv
Pythonの仮想環境

`sudo apt update`

必要なパッケージ

`sudo apt install build-essential libffi-dev libssl-dev zlib1g-dev liblzma-dev libbz2-dev libreadline-dev libsqlite3-dev libopencv-dev tk-dev git`

pyenvのクローン

`git clone https://github.com/pyenv/pyenv.git ~/.pyenv`

pyenvの環境変数

```terminal
echo '' >> ~/.bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
source ~/.bashrc
```

インストール確認

`pyenv -v`

適当なバージョンをインストール

`pyenv install -l`

`pyenv install 3.10.13`

ローカルフォルダにバージョンを設定

`pyenv local 3.10.13`

`pyenv versions`

もしかしたここでエディタの再起動必要かも

### Chrome + ChromeDriver
seleniumを動かすために必要

まずは適当なディレクトリに移動してからChromeをインストール

```terminal
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install
```

Chromeのバージョンに合ったDriverを落とす

```
pip install chromedriver-binary-auto
```

pythonにライブラリとしてインポート

`import chromedriver_binary`

<!-- ダウンロードしたものを解凍して/usr/local/binに移動

```
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin
sudo chmod +x /usr/local/bin/chromedriver
```

インストール確認

`chromedriver --version` -->


### selenium
`pip install selenium`

### discord
`pip install -U discord.py`

### BeautifulSoup4
`pip install beautifulsoup4`

### Pandas
`pip install pandas`

### Pythonライブラリをまとめてインストール
`pip install -U selenium discord.py beautifulsoup4 pandas`