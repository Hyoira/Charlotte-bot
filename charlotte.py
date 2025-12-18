import discord
from discord import app_commands, embeds
from discord.ext import tasks
import os
from get_latest_news import Scrape, Convert, UpdateCheck
import dotenv
import datetime
import asyncio
import functools

# 環境変数の読み込み
dotenv.load_dotenv(override=True)
token = os.getenv('BOT_TOKEN')
channel_ids = [int(cid) for cid in os.getenv('CHANNEL_IDS', '').split(',') if cid.strip()]
print('ChannelIds:', channel_ids)

# 必要な intents を設定
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# intents を渡して Bot インスタンスを作成
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ギルドIDを環境変数から取得（カンマ区切りで複数対応）
guild_ids = [int(gid) for gid in os.getenv('GUILD_IDS', '').split(',') if gid.strip()]
guild_objects = [discord.Object(id=gid) for gid in guild_ids]
print('GuildIds:', guild_ids)

# チャンネルをキャッシュしておく辞書
cached_channels = {}

# コマンド定義（全てのギルドで即時反映）
@tree.command(name="callcharlotte", description="Pong!")
async def callcharlotte_command(interaction: discord.Interaction):
    await interaction.response.send_message("しゃるぼっとよ‼️", ephemeral=True)

@tree.command(name="test", description="テストコマンドです。")
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("てすとよ！", ephemeral=True)

@tree.command(name='testremind', description='エスコフィエの料理マシナリーを呼び出す')
async def test_remind(interaction: discord.Interaction):
    await interaction.response.send_message("エスコフィエの料理マシナリーを呼び出すわよ！", ephemeral=True)
    await remind_escoffier_test(interaction.channel)

@tree.command(name='test_fetch', description='ニュースとHoYoLAB記事の取得をテスト実行します')
async def test_fetch(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    # Run Generic News Check
    updates_news = await client.loop.run_in_executor(None, run_scrape_and_check)
    news_count = len(updates_news) if updates_news is not None and not updates_news.empty else 0
    
    # Run HoYoLAB Check
    updates_hoyolab = await client.loop.run_in_executor(None, run_scrape_hoyolab_and_check)
    hoyolab_count = len(updates_hoyolab) if updates_hoyolab is not None and not updates_hoyolab.empty else 0

    await interaction.followup.send(
        f"取得テスト完了！\n公式ニュース: {news_count}件\nHoYoLAB: {hoyolab_count}件\n(新規があればチャンネルに送信されます)", 
        ephemeral=True
    )

    # Note: The existing logic inside run_scrape_and_check/run_scrape_hoyolab_and_check 
    # returns the updates but DOES NOT send them to Discord unless called by the task loop's checking logic.
    # WE need to manually send them here if we want immediate feedback in the channel, 
    # OR we rely on the side effect that `run_scrape...` updates the CSV, 
    # so the NEXT automatic check would miss them (since they are now in CSV).
    # Wait, `run_scrape_and_check` returns `updates`. The task loop `check_updates` uses that return value to send messages.
    # So if we run it here, we get the updates, but they are NOT sent to the channel automatically by the function itself.
    # We must send them manually here if we want them to appear.
    
    channel = interaction.channel
    
    if updates_news is not None and not updates_news.empty:
        for row in updates_news.to_dict(orient='records'):
            embed = discord.Embed(
                title=row['Title'].replace('<n>', '\n'),
                url=row['URL'],
                description=row['Summary'].replace('<n>', '\n'),
                color=0x00bfff)
            embed.set_image(url=row['Cover Image'])
            await channel.send(embed=embed)
            
    if updates_hoyolab is not None and not updates_hoyolab.empty:
        for row in updates_hoyolab.to_dict(orient='records'):
            embed = discord.Embed(
                title=row['Title'].replace('<n>', '\n'),
                url=row['URL'],
                description=row['Summary'].replace('<n>', '\n'),
                color=0xFFA500)
            embed.set_author(name="HoYoLAB Update", icon_url="https://media.discordapp.net/attachments/110000000000000000/110000000000000000/hoyolab_icon.png")
            embed.set_image(url=row['Cover Image'])
            await channel.send(embed=embed)

# on_readyで各ギルドごとに同期
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    for cid in channel_ids:
        try:
            channel = await client.fetch_channel(cid)
            cached_channels[cid] = channel
            print(f"チャンネル「{channel.name}」({cid}) が見つかりました")
        except Exception as e:
            print(f"チャンネルID {cid} の取得に失敗: {e}")
    if not remind_escoffier.is_running():
        remind_escoffier.start()
    if not remind_spiral.is_running():
        remind_spiral.start()
    if not check_updates.is_running():
        check_updates.start()
    if not check_hoyolab_updates.is_running():
        check_hoyolab_updates.start()

    # 各ギルドごとにコマンド同期
    for guild in guild_objects:
        # コマンドを追加
        # tree.add_command(callcharlotte_command, guild=guild)
        # tree.add_command(test_command, guild=guild)
        # tree.add_command(test_remind, guild=guild)
        try:
            # tree.add_command(test_fetch, guild=guild) # Add this if you want it enabled per guild immediately on restart
            tree.copy_global_to(guild=guild)
            synced = await tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands for guild {guild.id}")
        except Exception as e:
            print(f"tree.sync()でエラー（guild {guild.id}）: {e}")

###
### ここから下がメインの処理
###


# ブロッキング処理をまとめた関数
def run_scrape_and_check():
    scraper = Scrape()
    html = scraper.scrape("https://genshin.hoyoverse.com/ja/news/")
    new_data = Convert.convert(html)
    checker = UpdateCheck()
    # 新しい更新がある行のみを取得
    updates = checker.check_for_updates('data_prev.csv', new_data)
    
    # データの保存や更新判定もここで行う（CSV書き込みもブロッキングなので）
    if not updates.empty:
        # 新しいデータをCSVファイルに保存 (次回更新チェック用)
        # Note: calling this inside the thread is safe as long as we don't have multiple threads writing to it.
        # Since check_updates is a single task, this is fine.
        new_data.to_csv('data_prev.csv', index=False)
        return updates
    return None

# HoYoLABのブロッキング処理
def run_scrape_hoyolab_and_check():
    scraper = Scrape()
    # HoYoLAB user post list
    url = "https://www.hoyolab.com/accountCenter/postList?id=1015537"
    html = scraper.scrape_wait(url, ".mhy-article-card")
    new_data = Convert.convert_hoyolab(html)
    checker = UpdateCheck()
    
    updates = checker.check_for_updates('hoyolab_data.csv', new_data)
    
    if not updates.empty:
        new_data.to_csv('hoyolab_data.csv', index=False)
        return updates
    return None

# ニュースの更新チェック
@tasks.loop(minutes=5)
async def check_updates():
    for cid in channel_ids:
        channel = cached_channels.get(cid)
        now = datetime.datetime.now()
        print('Checking for updates...{0: %m/%d %H:%M}'.format(now))

        # ブロッキング処理を別スレッドで実行
        updates = await client.loop.run_in_executor(None, run_scrape_and_check)

        if updates is not None and not updates.empty:
            
            # Discordに埋め込みメッセージとして送信
            for row in updates.to_dict(orient='records'):
                embed = discord.Embed(
                    title=row['Title'].replace('<n>', '\n'),
                    url=row['URL'],
                    description=row['Summary'].replace('<n>', '\n'),
                    color=0x00bfff)
                if row.get('Cover Image'):
                    embed.set_image(url=row['Cover Image'])
                await channel.send(embed=embed)
        else:
            print(f"No updates for channel {cid}")


# HoYoLABの更新チェック
@tasks.loop(minutes=30) # 頻度はお好みで
async def check_hoyolab_updates():
    for cid in channel_ids:
        channel = cached_channels.get(cid)
        now = datetime.datetime.now()
        print('Checking for HoYoLAB updates...{0: %m/%d %H:%M}'.format(now))

        updates = await client.loop.run_in_executor(None, run_scrape_hoyolab_and_check)

        if updates is not None and not updates.empty:
            for row in updates.to_dict(orient='records'):
                embed = discord.Embed(
                    title=row['Title'].replace('<n>', '\n'),
                    url=row['URL'],
                    description=row['Summary'].replace('<n>', '\n'),
                    color=0xFFA500) # Orange for HoYoLAB
                embed.set_author(name="HoYoLAB Update", icon_url="https://media.discordapp.net/attachments/110000000000000000/110000000000000000/hoyolab_icon.png") # Optional customization
                if row.get('Cover Image'):
                    embed.set_image(url=row['Cover Image'])
                await channel.send(embed=embed)
        else:
            print(f"No HoYoLAB updates for channel {cid}")


###
### エスコリマインダー
###
# 毎週月曜日の朝7時にエスコフィエの料理マシナリーを起動するリマインダー
@tasks.loop(minutes=1)
async def remind_escoffier():
    now = datetime.datetime.now()
    # 月曜日かつ7:00ちょうどのみ送信
    if now.weekday() == 0 and now.hour == 7 and now.minute == 0:
        for cid in channel_ids:
            channel = cached_channels.get(cid)
            embed = discord.Embed(title="エスコフィエの料理マシナリーは呼び出したかしら？",
                                description="おはよう、月曜日ね！\nエスコフィエさんに料理をつくってもらうのを忘れずにね！")

            embed.set_image(url="https://upload-os-bbs.hoyolab.com/upload/2025/05/07/9fb3cbb05efb49894f0ce6356b1cb78f_6508162176253225300.png")

            await channel.send(embed=embed)
# 手動実行テスト用
async def remind_escoffier_test(channel):
    embed = discord.Embed(
        title="エスコフィエの料理マシナリーは呼び出したかしら？",
        description="おはよう、月曜日ね！\nエスコフィエさんに料理をつくってもらうのを忘れずにね！")

    embed.set_image(url="https://upload-os-bbs.hoyolab.com/upload/2025/05/07/9fb3cbb05efb49894f0ce6356b1cb78f_6508162176253225300.png")

    await channel.send(embed=embed)


###
### 螺旋リマインダー
### 毎月15日の朝7時に螺旋のリマインダーを起動する
###
@tasks.loop(minutes=1)
async def remind_spiral():
    now = datetime.datetime.now()
    today = now.date()
    # Check for the 15th (deadline for 16th reset)
    is_mid_month = (now.day == 15)
    
    # Check for the last day of the month (deadline for 1st reset)
    # The deadline is the day BEFORE the 1st of the next month.
    tomorrow = today + datetime.timedelta(days=1)
    is_end_month = (tomorrow.day == 1)

    if (is_mid_month or is_end_month) and now.hour == 7 and now.minute == 0:
        for cid in channel_ids:
            channel = cached_channels.get(cid)
            embed = discord.Embed(title="今月の螺旋は終わったかしら？",
                                description="おはよう、今月の螺旋も最終日ね！\n報酬の受け取りも忘れないように！")

            embed.set_image(url="https://upload-os-bbs.hoyolab.com/upload/2024/04/09/618ddb0165a9d25a0a688be152e45980_375351273206424725.jpg")

            await channel.send(embed=embed)


# Botのトークンを環境変数から取得して実行
client.run(token)
