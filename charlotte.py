import discord
from discord import app_commands, embeds
from discord.ext import tasks
import os
from get_latest_news import Scrape, Convert, UpdateCheck
import dotenv
import datetime

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

# コマンド定義（全てのギルドで即時反映）
for guild in guild_objects:
    @tree.command(name="callcharlotte", description="Pong!", guild=guild)
    async def callcharlotte_command(interaction: discord.Interaction):
        await interaction.response.send_message("しゃるぼっとよ‼️", ephemeral=True)

    @tree.command(name="test", description="テストコマンドです。", guild=guild)
    async def test_command(interaction: discord.Interaction):
        await interaction.response.send_message("てすとよ！", ephemeral=True)

    @tree.command(name='testremind', description='エスコフィエの料理マシナリーを呼び出す', guild=guild)
    async def test_remind(interaction: discord.Interaction):
        await interaction.response.send_message("エスコフィエの料理マシナリーを呼び出すわよ！", ephemeral=True)
        await remind_escoffier_test()

# on_readyで各ギルドごとに同期
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    for cid in channel_ids:
        try:
            channel = await client.fetch_channel(cid)
            print(f"チャンネル「{channel.name}」({cid}) が見つかりました")
        except Exception as e:
            print(f"チャンネルID {cid} の取得に失敗: {e}")
    remind_escoffier.start()

    # 各ギルドごとにコマンド同期
    for guild in guild_objects:
        try:
            synced = await tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands for guild {guild.id}")
        except Exception as e:
            print(f"tree.sync()でエラー（guild {guild.id}）: {e}")

###
### ここから下がメインの処理
###


# ニュースの更新チェック
@tasks.loop(seconds=30)
async def check_updates():
    for cid in channel_ids:
        channel = await client.fetch_channel(cid)
        now = datetime.datetime.now()
        print('Checking for updates...{0: %m/%d %H:%M}'.format(now))

        scraper = Scrape()
        html = scraper.scrape("https://genshin.hoyoverse.com/ja/news/")
        new_data = Convert.convert(html)
        checker = UpdateCheck()

        # 新しい更新がある行のみを取得
        updates = checker.check_for_updates('data_prev.csv', new_data)
        
        if not updates.empty:
            # 新しいデータをCSVファイルに保存 (次回更新チェック用)
            new_data.to_csv('data_prev.csv', index=False)

            # Discordに埋め込みメッセージとして送信
            for row in updates.to_dict(orient='records'):
                embed = discord.Embed(
                    title=row['Title'].replace('<n>', '\n'),
                    url=row['URL'],
                    description=row['Summary'].replace('<n>', '\n'),
                    color=0x00bfff)
                embed.set_image(url=row['Cover Image'])
                await channel.send(embed=embed)
        else:
            print(f"No updates for channel {cid}")


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
            channel = await client.fetch_channel(cid)
            embed = discord.Embed(title="エスコフィエの料理マシナリーは呼び出したかしら？",
                                description="おはよう、月曜日ね！\nエスコフィエさんに料理をつくってもらうのを忘れずにね！")

            embed.set_image(url="https://upload-os-bbs.hoyolab.com/upload/2025/05/07/9fb3cbb05efb49894f0ce6356b1cb78f_6508162176253225300.png")

            await channel.send(embed=embed)
# 手動実行テスト用
async def remind_escoffier_test():
    channel = await client.fetch_channel(channel_ids[0])
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
    if now.day == 15 and now.hour == 7 and now.minute == 0:
        for cid in channel_ids:
            channel = await client.fetch_channel(cid)
            embed = discord.Embed(title="今月の螺旋は終わったかしら？",
                                description="おはよう、今月の螺旋も最終日ね！\n報酬の受け取りも忘れないように！")

            embed.set_image(url="https://upload-os-bbs.hoyolab.com/upload/2024/04/09/618ddb0165a9d25a0a688be152e45980_375351273206424725.jpg")

            await channel.send(embed=embed)


# Botのトークンを環境変数から取得して実行
client.run(token)
