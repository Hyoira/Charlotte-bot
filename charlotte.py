import discord
from discord.ext import commands, tasks
import asyncio
import os
from get_latest_news import Scrape, Convert, UpdateCheck
import dotenv
dotenv.load_dotenv(override=True)


# 環境変数
token = os.getenv('BOT_TOKEN')
channel_id = int(os.getenv('CHANNEL_ID'))

print(os.getenv('CHANNEL_ID'))

# 必要な intents を設定
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# intents を渡して Bot インスタンスを作成
# bot = commands.Bot(command_prefix='!', intents=intents)
client = discord.Client(intents=intents)

# ログイン時にターミナルに通知する
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')

    try:
        channel = await client.fetch_channel(channel_id)
    except discord.NotFound:
        print(f"指定されたIDのチャンネルが見つかりません: {channel_id}")
        return
    except discord.HTTPException as e:
        print(f"チャンネルの取得に失敗しました: {e}")
        return
    print(f"チャンネル「{channel.name}」が見つかりました")
    check_updates.start()
        


@tasks.loop(seconds=60)
async def check_updates():
    channel = await client.fetch_channel(channel_id)
    print('Checking for updates...')

    Scrape()
    new_data = Convert.articles
    checker = UpdateCheck()

    # 新しい更新がある行のみを取得
    updates = checker.check_for_updates('data_prev.csv', new_data)
    
    if not updates.empty:
        # 新しいデータをCSVファイルに保存、次回更新チェック用
        new_data.to_csv('data_prev.csv', index=False)

        for index, row in updates.iterrows():
            embed = discord.Embed(
                title=row['Title'],
                url=row['URL'],
                description=row['Summary'],
                color=0x00bfff)
            embed.set_image(url=row['Cover Image'])
            await channel.send(embed=embed)
    else:
        print("No updates")

@client.event
async def on_message(message):
    if message.content == '!ping':
        await message.channel.send('pong')


# Botのトークンを環境変数から取得して実行
client.run(token)
