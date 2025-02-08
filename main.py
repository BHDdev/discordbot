import discord
from discord.ext import commands
import dotenv
import os
from configman import config
import logging

dotenv.load_dotenv()

# Constants
PINUP_ROLL_ID = int(config["pinup_role_id"])

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
    # print("Bot is ready")
    logging.info("Bot is ready")
    for filename in os.listdir("./cogs"):
        if filename.endswith("py"):
            logging.info(f"Loading cog {filename}")
            await bot.load_extension(f"cogs.{filename[:-3]}")
    try:
        synced = await bot.tree.sync()
        # print(f"Synced {len(synced)} commands")
        logging.info(f"Synced {len(synced)} commands")
    except Exception as e:
        # print(f"Failed to sync commands: {e}")
        logging.exception("Failed to sync commands")


# Thread management commands
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    # print(f"{user} reacted with {reaction.emoji}")
    logging.debug(f"{user} reacted with {reaction.emoji}")
    if (
        reaction.message.channel.type == discord.ChannelType.private_thread
        or reaction.message.channel.type == discord.ChannelType.public_thread
    ):
        if reaction.message.channel.owner == user:
            # print("User is the owner of the thread")
            logging.debug(f"User {user} is the owner of the thread")
            if reaction.emoji == "🔒":
                # print("Locking thread")
                logging.info(f"Locking thread {reaction.message.channel.id}")
                await reaction.message.channel.edit(archived=True)
            elif reaction.emoji == "🔓":
                # print("Unlocking thread")
                logging.info(f"Unlocking thread {reaction.message.channel.id}")
                await reaction.message.channel.edit(archived=False)
            elif reaction.emoji == "📌":
                # print("Pinning message")
                logging.info(f"Pinning message {reaction.message.id}")
                await reaction.message.pin()
            elif reaction.emoji == "📍":
                # print("Unpinning message")
                logging.info(f"Unpinning message {reaction.message.id}")
                await reaction.message.unpin()

    if any(role.id == PINUP_ROLL_ID for role in user.roles):
        if reaction.emoji == "📌":
            # print("Pinning message")
            logging.info(f"Pinning message {reaction.message.id}")
            await reaction.message.pin()
        elif reaction.emoji == "📍":
            # print("Unpinning message")
            logging.info(f"Unpinning message {reaction.message.id}")
            await reaction.message.unpin()


# Welcome message
@bot.event
async def on_member_join(member: discord.Member):
    channel = member.guild.system_channel
    if channel:
        await channel.send(f"Ahh {member.mention}, we have been expecting you...")


# Example slash commands
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True, delete_after=5)


# System management commands
@bot.tree.command(name="update")
@commands.has_permissions(administrator=True)
async def update(interaction: discord.Interaction):
    await interaction.response.send_message("Updating bot...", ephemeral=True)
    os.system(
        "git config --global --add safe.directory '*'"
    )  # just dont do this to your dev machine
    os.system("git pull")
    await interaction.followup.send("Bot updated. Restarting...", ephemeral=True)
    await bot.close()


@bot.tree.command(name="downloadconfig")
@commands.has_permissions(administrator=True)
async def downloadconfig(interaction: discord.Interaction):
    await interaction.response.send_message("Downloading config...", ephemeral=True)
    await interaction.followup.send(file=discord.File("config.json"), ephemeral=True)


@bot.tree.command(name="uploadconfig")
@commands.has_permissions(administrator=True)
@discord.app_commands.describe(file="The config file to upload")
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
    embed.add_field(name="update", value="Update the bot", inline=False)
    embed.add_field(name="imhelp", value="Info to ims", inline=False)
    embed.add_field(name="role", value="Manage roles", inline=False)
    embed.add_field(
        name="Reaction commands",
        value="📌 Pin message\n📍 Unpin message\n🔒 Lock thread\n🔓 Unlock thread",
        inline=False,
    )

    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)


bot.run(os.getenv("DISCORD_TOKEN"))
