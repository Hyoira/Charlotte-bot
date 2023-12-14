import discord
from discord.ext import tasks
import config


# トークンの読み込み
token = config.BOT_TOKEN

# チャンネルIDの読み込み
channel_id = config.CHANNEL_ID

# インテントの生成
intents = discord.Intents.default()
intents.message_content = True

# クライアントの生成
client = discord.Client(intents=intents)


# 60秒に一回ループ
@tasks.loop(seconds=60)
async def loop():
    # botが起動するまで待つ
    await client.wait_until_ready()
    channel = client.get_channel(channel_id)
    await channel.send('時間だよ')  

#ループ処理実行
loop.start()

client.run(token)