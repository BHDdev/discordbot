import discord
from discord.ext import commands
from discord import app_commands
import logging
import aiohttp
from configman import config


class Embedder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embed")
    async def embed(
        self,
        interaction: discord.Interaction,
        sensitive: bool = False,
    ):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config['embedder_endpoint']}/api/new-id", headers={"Authorization": f"Bearer {config['embedder_token']}"}) as response:
                data = await response.json()
        url = data.get("url")
        if not url:
            await interaction.response.send_message("Failed to create upload url.", ephemeral=True)
            return

        done_button = discord.ui.Button(label="Done", style=discord.ButtonStyle.primary)
        async def done_callback(interaction: discord.Interaction):
            if sensitive:
                embed = discord.Embed(description="Upload finished")
                embed.set_image(url=f"{config['embedder_endpoint']}{url}")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"{config['embedder_endpoint']}{url}")
        done_button.callback = done_callback

        view = discord.ui.View()
        view.add_item(done_button)
        
        embed = discord.Embed(title="File Upload", description="Click the button below when you have finished uploading your content.", color=discord.Color.blue())
        embed.add_field(name="Upload URL", value=f"{config['embedder_endpoint']}{url}", inline=False)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True, delete_after=300)

async def setup(bot):
    await bot.add_cog(Embedder(bot))
    logging.info("Embedder cog loaded")
