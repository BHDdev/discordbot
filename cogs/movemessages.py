import discord
from discord.ext import tasks, commands
from discord import app_commands
import logging


class MoveMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @app_commands.command(name="pingcog")
    # async def pingcog(self, interaction: discord.Interaction):
    #    await interaction.response.send_message("Pong!", ephemeral=True, delete_after=5)


async def setup(bot):
    await bot.add_cog(MoveMessages(bot))
    logging.info("MoveMessages cog loaded")
