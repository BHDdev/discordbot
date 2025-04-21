import discord
from discord.ext import commands
import re
import random
import aiohttp
import logging


# Cat gifs (very important XD)
class CatGifView(discord.ui.View):
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Deleting...", ephemeral=True, delete_after=2
        )
        await interaction.message.delete()


class CatGif(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if "cat" in message.content:
            # 1 in 20 chance to send a cat gif
            if random.randint(1, 20) == 1:
                queryurl = (
                    "https://g.tenor.com/v1/search?q=cat&key=LIVDSRZULELA&limit=8"
                )
                async with aiohttp.ClientSession() as session:
                    async with session.get(queryurl) as response:
                        data = await response.json()
                # result = requests.get(queryurl)
                # data = result.json()
                gifs = data["results"]
                gif = random.choice(gifs)
                view = CatGifView()
                await message.channel.send(gif["media"][0]["gif"]["url"], view=view)
        if re.search(r"\b\d{3}\b", message.content):
            if random.randint(1, 4) == 1:
                number = re.search(r"\b\d{3}\b", message.content).group()
                queryurl = f"https://http.cat/{number}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(queryurl) as response:
                        if response.status == 200:
                            view = CatGifView()
                            await message.channel.send(queryurl, view=view)

                # result = requests.get(queryurl)
                # if result.status_code == 200:
                #     view = CatGifView()
                #     await message.channel.send(queryurl, view=view)


async def setup(bot):
    await bot.add_cog(CatGif(bot))
    logging.info("CatGif cog loaded")
