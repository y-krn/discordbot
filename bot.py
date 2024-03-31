import discord
from discord.ext import tasks
import feedparser
import anthropic
import os
import requests
from bs4 import BeautifulSoup


# Discord Bot token
TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(
    os.environ.get("CHANNEL_ID")
)  # Discord channel ID to send the summary to

# RSS feed URL to monitor
RSS_FEED_URL = "http://b.hatena.ne.jp/hotentry/it.rss"

# Discord client initialization
intents = discord.Intents.default()
client = discord.Client(intents=intents)

anthclient = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)


# Task to fetch and process the RSS feed
@tasks.loop(minutes=30)
async def rss_task():
    feed = feedparser.parse(RSS_FEED_URL)

    # Process each feed entry
    for entry in feed.entries:
        article_url = entry.link
        title = entry.title

        try:
            response = requests.get(article_url)
            html_content = response.text
        except:
            print("記事の取得に失敗しました。")
            continue

        # BeautifulSoupを使って本文のみを抽出
        soup = BeautifulSoup(html_content, "html.parser")
        article_body = [c.get_text() for c in soup.find_all("p")]
        # 本文を含むDivタグの例
        if article_body:
            content = " ".join(article_body)
        else:
            print("本文の抽出に失敗しました。")
            continue

        # Use Claude API to summarize the content
    message = anthclient.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4096,
        temperature=0,
        system="次のテキストから重要なポイントを5つ抽出し、各々箇条書きで5点まとめてください。",
        messages=[{"role": "user", "content": [{"type": "text", "text": content}]}],
    )

    # Send the summary to the Discord channel
    channel = client.get_channel(CHANNEL_ID)
    await channel.send(f"**{title}**\n{article_url}\n{message.content}")


# Start the RSS task when the bot is ready
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    rss_task.start()


# Run the bot
client.run(TOKEN)
