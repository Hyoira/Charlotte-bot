import discord
from discord.ext import tasks
import config
import comparator
import asyncio

# トークンの読み込み
token = config.BOT_TOKEN

# チャンネルIDの読み込み
channel_id = config.CHANNEL_ID

# インテントの生成
intents = discord.Intents.default()
intents.message_content = True

# クライアントの生成
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')

    channel = await client.fetch_channel(channel_id)

    if not channel:
        print(f"指定されたIDのチャンネルが見つかりません: {config.CHANNEL_ID}")
    else:
        print(f"チャンネル「{channel.name}」が見つかりました")
        loop.start()  # チャンネルが見つかったときのみタスクを開始


@tasks.loop(seconds=60)
async def loop():
    await client.wait_until_ready()
    entries_new = None
    channel = await client.fetch_channel(channel_id)

    try:
        comp = comparator.Comparator()
        entries_new = comp.entries_new

        if not entries_new.empty:
            entries_new = entries_new.reset_index(drop=True)
            print(f'{len(entries_new)}個の新着記事があります!!')

            for index, row in entries_new.iterrows():
                embed = discord.Embed(
                    title=row['Title'],
                    url=row['URL'],
                    description=row['Summary'],
                    color=0x00bfff)
                embed.set_image(url=row['Cover Image'])
                await channel.send(embed=embed)
        else:
            print('新着記事はありません')

    except Exception as e:  # ここで発生した例外の種類とメッセージを出力
        print(f'エラーが発生しました: {e}')
        await channel.send('エラーが発生しました。詳細はログを確認してください。')


client.run(token)