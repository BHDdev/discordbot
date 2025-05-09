import discord
from discord.ext import commands
from discord import app_commands
import dotenv
import os
from configman import init, config
import logging

dotenv.load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix=(),
    description="Community made BHD discord bot. Licensed under the AGPL.",
    intents=intents,
    help_command=None,
)


# Sync commands on ready
@bot.event
async def on_ready():
    logging.info("Bot is ready")
    for filename in os.listdir("./cogs"):
        if filename.endswith("py"):
            logging.info(f"Loading cog {filename}")
            await bot.load_extension(f"cogs.{filename[:-3]}")
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logging.exception(f"Failed to sync commands: {e}")
    init()


# Welcome message
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # Check if the member has completed onboarding
    if after.flags.completed_onboarding and not before.flags.completed_onboarding:
        channel = bot.get_channel(config["welcome_message"]["channel_id"])
        if channel:
            await channel.send(config["welcome_message"]["message"] % after.mention)


# Example slash commands
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True, delete_after=5)


# System management commands
@bot.tree.command(name="update")
@app_commands.checks.has_permissions(administrator=True)
async def update(interaction: discord.Interaction):
    await interaction.response.send_message("Updating bot...", ephemeral=True)
    os.system(
        "git config --global --add safe.directory '*'"
    )  # just dont do this to your dev machine
    os.system("git pull")
    await interaction.followup.send("Bot updated. Restarting...", ephemeral=True)
    await bot.close()


@bot.tree.command(name="downloadconfig")
@app_commands.checks.has_permissions(administrator=True)
async def downloadconfig(interaction: discord.Interaction):
    await interaction.response.send_message("Downloading config...", ephemeral=True)
    await interaction.followup.send(file=discord.File("config.json"), ephemeral=True)


@bot.tree.command(name="uploadconfig")
@app_commands.checks.has_permissions(administrator=True)
async def uploadconfig(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.send_message("Uploading config...", ephemeral=True)
    with open("config.json", "wb") as f:
        f.write(await file.read())
    await interaction.followup.send("Config uploaded", ephemeral=True)


# help command
@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="GitHub repository",
            url="https://github.com/BHDdev/discordbot",
            style=discord.ButtonStyle.link,
        )
    )

    embed = discord.Embed(
        title="BHD Bot Help",
        description="Community made BHD discord bot. Licensed under the AGPL.",
        color=discord.Color.blue(),
    )
    embed.add_field(name="ping", value="Pong!", inline=False)
    embed.add_field(name="imhelp", value="Info to ims", inline=False)
    embed.add_field(name="role", value="Manage roles", inline=False)
    embed.add_field(
        name="Reaction commands",
        value="📌 Pin message\n📍 Unpin message\n🔒 Lock thread\n🔓 Unlock thread",
        inline=False,
    )
    embed.add_field(
        name="Vote pinning",
        value="5 📌 will get a message pinned.\nIf the message collects 5 more 📍 than 📌 , then its unpinned again.\nIf the message contains !NP! it isnt affected.",
        inline=False,
    )

    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)


# Error handling
@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
    else:
        logging.error(f"Command error: {error}")


bot.run(os.getenv("DISCORD_TOKEN"))
