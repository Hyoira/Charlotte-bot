import discord
from discord import app_commands, embeds
from datetime import time, timezone, timedelta
from discord.ext import tasks
import os
from get_latest_news import UpdateCheck, GameNews
from dotenv import load_dotenv
import datetime
import asyncio
import functools

# Timezone Definition
JST = timezone(timedelta(hours=9), 'Asia/Tokyo')

# 環境変数の読み込み
load_dotenv(override=True)
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




@tree.command(name="test_fetch", description="最新のゲーム内お知らせを1件取得して送信します")
async def test_fetch(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Fetch latest news
        game_news = GameNews.fetch_announcements()
        
        if not game_news.empty:
            # Get the first (latest) item
            row = game_news.iloc[0]
            
            title = row['Title']
            summary = row['Summary']
            banner_url = row['Cover Image']
            url = row.get('URL', '')
            
            description = f"{summary}"
            
            # 期間表示の追加
            start_ts = row.get('start_timestamp')
            end_ts = row.get('end_timestamp')
            
            try:
                start_ts = int(float(start_ts)) if start_ts else 0
                end_ts = int(float(end_ts)) if end_ts else 0
            except (ValueError, TypeError):
                pass

            if start_ts > 0:
                description += f"\n\n**期間**: <t:{start_ts}:f>"
                if end_ts > 0:
                    description += f" ~ <t:{end_ts}:f>"
            
            embed = discord.Embed(
                title=f"{title}", 
                description=description,
                url=url if url else None,
                color=0x00b0f4 # Genshin Blue-ish
            )
            
            if banner_url:
                embed.set_image(url=banner_url)

            embed.set_footer(text="しゃるぼっとがお届けします！")
            embed.timestamp = datetime.datetime.now(JST)
            
            # Send to the channel where command was invoked
            await interaction.channel.send(embed=embed)
            
            await interaction.followup.send(
                f"最新のお知らせを送信しました。", 
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "お知らせが見つかりませんでした。", 
                ephemeral=True
            )
    except Exception as e:
        await interaction.followup.send(
            f"エラーが発生しました: {e}", 
            ephemeral=True
        )

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
    if not check_game_news_updates.is_running():
        check_game_news_updates.start()

    # 各ギルドごとにコマンド同期
    for guild in guild_objects:
        # コマンドを追加
        try:
            # tree.add_command(test_fetch, guild=guild) # Add this if you want it enabled per guild immediately on restart
            tree.copy_global_to(guild=guild)
            synced = await tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands for guild {guild.id}")
        except Exception as e:
            print(f"tree.sync()でエラー（guild {guild.id}）: {e}")




@tasks.loop(minutes=10)
async def check_game_news_updates():
    now = datetime.datetime.now(JST)
    print(f"Checking for Game News updates... {now.strftime('%m/%d %H:%M')}")
    
    # 全部のチャンネルに対して通知するのは既存のロジックと同じ
    try:
        game_news = GameNews.fetch_announcements()
        
        # CSVファイルパス
        csv_path = os.path.abspath('game_announcements.csv')

        updates = UpdateCheck.check_for_updates(csv_path, game_news, merge_keys=["ann_id"])
        
        # データの保存
        game_news.to_csv(csv_path, index=False)

        for cid in channel_ids:
            channel = client.get_channel(cid)
            if channel is None:
                print(f"Channel not found: {cid}")
                continue

            if updates is not None and not updates.empty:
                for row in updates.to_dict(orient='records'):
                    # Embedの作成
                    title = row['Title']
                    summary = row['Summary']
                    banner_url = row['Cover Image']
                    url = row.get('URL', '')
                    
                    description = f"{summary}"
                    
                    # 期間表示の追加
                    start_ts = row.get('start_timestamp')
                    end_ts = row.get('end_timestamp')
                    
                    # start_timestamp, end_timestamp は floatの可能性もあるため intに変換
                    try:
                        start_ts = int(float(start_ts)) if start_ts else 0
                        end_ts = int(float(end_ts)) if end_ts else 0
                    except (ValueError, TypeError):
                        pass

                    if start_ts > 0:
                        description += f"\n\n**期間**: <t:{start_ts}:f>"
                        if end_ts > 0:
                            description += f" ~ <t:{end_ts}:f>"
                    
                    embed = discord.Embed(
                        title=f"{title}", 
                        description=description,
                        url=url if url else None,
                        color=0x00b0f4 # Genshin Blue-ish
                    )
                    
                    if banner_url:
                        embed.set_image(url=banner_url)

                    embed.set_footer(text="Genshin Impact Game Announcement")
                    embed.timestamp = datetime.datetime.now(JST)
                    
                    await channel.send(embed=embed)
            else:
                print(f"No Game News updates for channel {cid}")

    except Exception as e:
        print(f"Error in check_game_news_updates: {e}")

###
### エスコリマインダー
###
# 毎週月曜日の朝7時にエスコフィエの料理マシナリーを起動するリマインダー
@tasks.loop(minutes=1)
async def remind_escoffier():
    now = datetime.datetime.now(JST)
    # 月曜日かつ7:00ちょうどのみ送信
    if now.weekday() == 0 and now.hour == 7 and now.minute == 0:
        for cid in channel_ids:
            channel = cached_channels.get(cid)
            embed = discord.Embed(title="エスコフィエの料理マシナリーは呼び出したかしら？",
                                description="おはよう、月曜日ね！\nエスコフィエさんに料理をつくってもらうのを忘れずにね！")

            embed.set_image(url="https://upload-os-bbs.hoyolab.com/upload/2025/05/07/9fb3cbb05efb49894f0ce6356b1cb78f_6508162176253225300.png")

            await channel.send(embed=embed)



###
### 螺旋リマインダー
### 毎月15日の朝7時に螺旋のリマインダーを起動する
###
@tasks.loop(minutes=1)
async def remind_spiral():
    now = datetime.datetime.now(JST)
    today = now.date()
    is_mid_month = (now.day == 15)

    if is_mid_month and now.hour == 7 and now.minute == 0:
        for cid in channel_ids:
            channel = cached_channels.get(cid)
            embed = discord.Embed(title="今月の螺旋は終わったかしら？",
                                description="おはよう、今月の螺旋も最終日ね！\n報酬の受け取りも忘れないように！")

            embed.set_image(url="https://upload-os-bbs.hoyolab.com/upload/2024/04/09/618ddb0165a9d25a0a688be152e45980_375351273206424725.jpg")

            await channel.send(embed=embed)


###
### 幻想シアターリマインダー
### 月末の朝7時に螺旋のリマインダーを起動する
###
@tasks.loop(minutes=1)
async def remind_theatre():
    now = datetime.datetime.now(JST)
    today = now.date()
    tomorrow = today + datetime.timedelta(days=1)
    is_end_month = (tomorrow.day == 1)

    if is_end_month and now.hour == 7 and now.minute == 0:
        for cid in channel_ids:
            channel = cached_channels.get(cid)
            image = discord.File("img/theatre.png")
            embed = discord.Embed(title="今月の幻想シアターは終わったかしら？",
                                description="おはよう、今月の幻想シアターも最終日ね！\n報酬の受け取りも忘れないように。\n来月のシアターの情報はこんな感じよ！")

            embed.set_image(url="attachment://theatre.png")

            await channel.send(embed=embed)


@tree.command(name="test_theatre", description="幻想シアターのリマインダーをテスト送信します")
async def test_theatre(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        file = discord.File("img/theatre.png", filename="theatre.png")
        embed = discord.Embed(
            title="今月の幻想シアターは終わったかしら？",
            description="おはよう、今月の幻想シアターも最終日ね！\n報酬の受け取りも忘れないように。\n来月のシアターの情報はこんな感じよ！"
        )
        # 添付ファイルを Embed に表示
        embed.set_image(url="attachment://theatre.png")

        await interaction.channel.send(embed=embed, file=file)
        await interaction.followup.send("テスト送信しました。", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"送信に失敗しました: {e}", ephemeral=True)



# Botのトークンを環境変数から取得して実行
client.run(token)
