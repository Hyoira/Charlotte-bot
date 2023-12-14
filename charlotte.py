import discord
from discord.ext import tasks
import config
import comparator


# トークンの読み込み
token = config.BOT_TOKEN

# チャンネルIDの読み込み
channel_id = config.CHANNEL_ID

# インテントの生成
intents = discord.Intents.default()
intents.message_content = True

# クライアントの生成
client = discord.Client(intents=intents)

# if entries_new.empty:
# print(entries_new["Title"])

"""
@tasks.loop(seconds=30)
async def loop():
    await client.wait_until_ready()
    channel = client.get_channel(channel_id)
    await channel.send('時間だよ')

#ループ処理実行
loop.start()

client.run(token)
"""

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content == '!test':
        # 新着記事を取得
        try:
            comp = comparator.Comparator()
            entries_new = comp.entries_new
            await message.channel.send('新着記事のチェックが完了しました!!')

            if not entries_new.empty:
               entries_new = entries_new.reset_index(drop=True)
        except: 
            await message.channel.send('エラーが発生しました。')
            return

        if entries_new.empty:
          await message.channel.send('新着記事はありません')
          return
        else:
          await message.channel.send(f'{len(entries_new)}個の新着記事があります!!')
          for index, row in entries_new.iterrows():
            embed = discord.Embed(
               title=row['Title'], 
               url=row['URL'], 
               description=row['Summary'], 
               color=0x00bfff)
            embed.set_image(url=row['Cover Image'])
            await message.channel.send(embed=embed)

client.run(token)