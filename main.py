import discord
from discord.ext import tasks, commands
import dotenv
import os

dotenv.load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=(), description="Community made BHD discord bot. Licensed under the AGPL.", intents=intents, help_command=None)

# Sync commands on ready
@bot.event
async def on_ready():
    print("Bot is ready")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Thread management commands
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    print(f"{user} reacted with {reaction.emoji}")
    if reaction.message.channel.type == discord.ChannelType.private_thread or reaction.message.channel.type == discord.ChannelType.public_thread:
        if reaction.message.channel.owner == user:
            print("User is the owner of the thread")
            if reaction.emoji == "🔒":
                print("Locking thread")
                await reaction.message.channel.edit(archived=True)
            elif reaction.emoji == "🔓":
                print("Unlocking thread")
                await reaction.message.channel.edit(archived=False)
            elif reaction.emoji == "📌":
                print("Pinning message")
                await reaction.message.pin()
            elif reaction.emoji == "📍":
                print("Unpinning message")
                await reaction.message.unpin()


# Example slash commands    
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True, delete_after=5)

#@bot.tree.command(name="echo")
#@discord.app_commands.describe(message = "The message to echo")
#async def echo(interaction: discord.Interaction, message: str):
#    await interaction.response.send_message(message, delete_after=5)

# System management commands
@bot.tree.command(name="update")
@commands.has_permissions(administrator=True)
async def update(interaction: discord.Interaction):
    await interaction.response.send_message("Updating bot...", ephemeral=True)
    os.system("git pull")
    await interaction.followup.send("Bot updated. Restarting...", ephemeral=True)
    await bot.close()

@bot.tree.command(name="addcontributor")
@commands.has_permissions(manage_roles=True, ban_members=True)
async def addcontributor(interaction: discord.Interaction, user: discord.User):
    # todo call out to github api to add user to contributors
    await interaction.response.send_message("WIP", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))