import discord
from discord.ext import commands
import re


class LinkPreview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Handler for embedding/previewing discord links in messages
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if "discord.com/channels" in message.content:
            match = re.search(
                r"discord.com/channels/(\d+)/(\d+)/(\d+)", message.content
            )
            message_id = match.group(3)
            channel_id = match.group(2)
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                foundmessage = await channel.fetch_message(int(message_id))
                if foundmessage:
                    embed = discord.Embed(
                        description=foundmessage.content, color=discord.Color.blurple()
                    )
                    embed.set_author(
                        name=foundmessage.author.name,
                        icon_url=foundmessage.author.avatar,
                    )
                    embed.timestamp = foundmessage.created_at
                    await message.reply(embed=embed, mention_author=False)


async def setup(bot):
    await bot.add_cog(LinkPreview(bot))
