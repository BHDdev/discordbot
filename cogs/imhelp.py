import discord
from discord.ext import commands
from configman import implantData
from discord import app_commands
from math import ceil
import logging


def generate_options(chunk_index: int):
    """Generate chunked select options for implants."""
    options = [
        discord.SelectOption(
            label=key, description=f"Pick this for more information on {key}"
        )
        for key in implantData
    ]

    chunked_options = []
    chunk_size = 25  # Discord's max options limit
    for i in range(0, len(options), chunk_size):
        chunked_options.append(options[i : i + chunk_size])
    return chunked_options[chunk_index]


class ImplantSelectView(discord.ui.View):
    def __init__(self, chunk_index: int):
        super().__init__()
        self.chunk_index = chunk_index
        options = generate_options(chunk_index)

        select = discord.ui.Select(
            placeholder="Select implants you'd like to view",
            min_values=1,
            max_values=len(options),
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        select = self.children[0]
        select.disabled = True
        await interaction.response.send_message(
            "Loading selected...", ephemeral=True, delete_after=1
        )

        for value in select.values:
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="More",
                    url=implantData[value]["url"],
                    style=discord.ButtonStyle.link,
                )
            )
            embed = discord.Embed(title=value, color=discord.Color.blurple())
            embed.description = implantData[value]["description"]
            embed.set_image(url=implantData[value]["image"])
            await interaction.followup.send(embed=embed, view=view)


class ImHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="imhelp")
    async def imhelp(self, interaction: discord.Interaction):
        """Display implant information selection menu."""
        chunk_size = 25
        total_chunks = ceil(len(implantData) / chunk_size)

        # Send initial response with first view
        await interaction.response.send_message(
            "Select which implants you'd like to view information about:",
            view=ImplantSelectView(0),
            ephemeral=True,
        )

        # Send additional chunks if needed
        for chunk_index in range(1, total_chunks):
            await interaction.followup.send(
                view=ImplantSelectView(chunk_index),
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(ImHelp(bot))
    logging.info("ImHelp cog loaded")
