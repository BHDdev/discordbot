import discord
from discord.ext import tasks, commands
import random
import requests
import dotenv
import re
import os

dotenv.load_dotenv()
PINUP_ROLL_ID = 1306182463508451339

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

    if any(role.id == PINUP_ROLL_ID for role in user.roles):
        if reaction.emoji == "📌":
            print("Pinning message")
            await reaction.message.pin()
        elif reaction.emoji == "📍":
            print("Unpinning message")
            await reaction.message.unpin()

# Cat gifs (very important XD)
class CatGifView(discord.ui.View):
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Deleting...", ephemeral=True, delete_after=2)
        await interaction.message.delete()

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if "cat" in message.content:
        # 1 in 4 chance to send a cat gif
        if random.randint(1, 4) == 1:
            queryurl = "https://g.tenor.com/v1/search?q=cat&key=LIVDSRZULELA&limit=8"
            result = requests.get(queryurl)
            data = result.json()
            gifs = data["results"]
            gif = random.choice(gifs)
            view = CatGifView()
            await message.channel.send(gif["media"][0]["gif"]["url"], view=view)
    if re.search(r"\b\d{3}\b", message.content):
        if random.randint(1, 4) == 1:
            number = re.search(r"\b\d{3}\b", message.content).group()
            queryurl = f"https://http.cat/{number}"
            result = requests.get(queryurl)
            if result.status_code == 200:
                view = CatGifView()
                await message.channel.send(queryurl, view=view)


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
    os.system("git config --global --add safe.directory '*'") # just dont do this to your dev machine
    os.system("git pull")
    await interaction.followup.send("Bot updated. Restarting...", ephemeral=True)
    await bot.close()


# help command
@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="GitHub repository", url="https://github.com/BHDdev/discordbot", style=discord.ButtonStyle.link))

    embed = discord.Embed(title="BHD Bot Help", description="Community made BHD discord bot. Licensed under the AGPL.", color=discord.Color.blue())
    embed.add_field(name="ping", value="Pong!", inline=False)
    embed.add_field(name="update", value="Update the bot", inline=False)
    embed.add_field(name="imhelp", value="Info to ims", inline=False)
    embed.add_field(name="Reaction commands", value="📌 Pin message\n📍 Unpin message\n🔒 Lock thread\n🔓 Unlock thread", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

# Im help
class ImHelpView(discord.ui.View):
    data = {
        "Strawberry": {
            "description": "Strawberry is a popular flavor!",
            "image": "https://unsplash.it/200/200",
            "url": "https://example.com"
        },
        "Chocolate": {
            "description": "Chocolate is a classic flavor!",
            "image": "https://unsplash.it/200/200",
            "url": "https://example.com"
        },
        "Vanilla": {
            "description": "Vanilla is a simple flavor!",
            "image": "https://unsplash.it/200/200",
            "url": "https://example.com"
        }
    }

    @discord.ui.select(
        placeholder = "Choose a Flavor!",
        min_values = 1,
        max_values= 3,
        options = [
            discord.SelectOption(
                label="Vanilla",
                description="Pick this if you like vanilla!"
            ),
            discord.SelectOption(
                label="Chocolate",
                description="Pick this if you like chocolate!"
            ),
            discord.SelectOption(
                label="Strawberry",
                description="Pick this if you like strawberry!"
            )
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.select):
        await interaction.response.send_message(f"Loading selected...", ephemeral=True, delete_after=1)
        for value in select.values:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="More", url=self.data[value]["url"], style=discord.ButtonStyle.link))
            embed = discord.Embed(title=value, color=discord.Color.blue())
            embed.description = self.data[value]["description"]
            embed.set_image(url=self.data[value]["image"])
            await interaction.followup.send(embed=embed, view=view)

    # Handler for embedding/previewing discord links in messages
    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return
        if "discord.com/channels" in message.content:
            match = re.search(r"discord.com/channels/(\d+)/(\d+)/(\d+)", message.content)
            message_id = match.group(3)
            channel_id = match.group(2)
            channel = bot.get_channel(int(channel_id))
            if channel:
                foundmessage = await channel.fetch_message(int(message_id))
                if foundmessage:
                    embed = discord.Embed(description=foundmessage.content, color=discord.Color.blurple())
                    embed.set_author(name=foundmessage.author.name, icon_url=foundmessage.author.avatar)
                    embed.timestamp = foundmessage.created_at
                    await message.reply(embed=embed, mention_author=False)


@bot.tree.command(name="imhelp")
async def imhelp(interaction: discord.Interaction):
    await interaction.response.send_message("Select of which youd like to view information", view=ImHelpView(), ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))