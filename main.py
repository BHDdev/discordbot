import discord
from discord.ext import tasks, commands
import random
import requests
import dotenv
import re
import os
import json
import shutil

dotenv.load_dotenv()

# load config file
if not os.path.exists("config.json"):
    # copy example config
    shutil.copy("config.example.json", "config.json")

with open("config.json", "r") as f:
    config = json.load(f)

# Constants
PINUP_ROLL_ID = int(config["pinup_role_id"])

# load data files
with open("implantData.json", "r", encoding="utf8") as f:
    implantData = json.load(f)

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
    update_OC_rankings.start()

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

# Welcome message
@bot.event
async def on_member_join(member: discord.Member):
    channel = member.guild.system_channel
    if channel:
        await channel.send(f"Ahh {member.mention}, we have been expecting you...")

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

@bot.tree.command(name="downloadconfig")
@commands.has_permissions(administrator=True)
async def downloadconfig(interaction: discord.Interaction):
    await interaction.response.send_message("Downloading config...", ephemeral=True)
    await interaction.followup.send(file=discord.File("config.json"), ephemeral=True)

@bot.tree.command(name="uploadconfig")
@commands.has_permissions(administrator=True)
@discord.app_commands.describe(file = "The config file to upload")
async def uploadconfig(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.send_message("Uploading config...", ephemeral=True)
    with open("config.json", "wb") as f:
        f.write(await file.read())
    await interaction.followup.send("Config uploaded", ephemeral=True)

# help command
@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="GitHub repository", url="https://github.com/BHDdev/discordbot", style=discord.ButtonStyle.link))

    embed = discord.Embed(title="BHD Bot Help", description="Community made BHD discord bot. Licensed under the AGPL.", color=discord.Color.blue())
    embed.add_field(name="ping", value="Pong!", inline=False)
    embed.add_field(name="update", value="Update the bot", inline=False)
    embed.add_field(name="imhelp", value="Info to ims", inline=False)
    embed.add_field(name="role", value="Manage roles", inline=False)
    embed.add_field(name="Reaction commands", value="📌 Pin message\n📍 Unpin message\n🔒 Lock thread\n🔓 Unlock thread", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

# Im help
def generate_options(chunckIndex: int):
    options = []
    for key in implantData:
        options.append(discord.SelectOption(label=key, description=f"Pick this for more information on {key}"))

    chunckedOptions = []
    for i in range(0, len(options), 25):
        chunckedOptions.append(options[i:i+25])
    return chunckedOptions[chunckIndex]
class ImHelpView(discord.ui.View):
    @discord.ui.select(
        placeholder = "Select implants youd like to view",
        min_values = 1,
        max_values = len(generate_options(0)),
        options = generate_options(0)
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.select):
        select.disabled = True
        await interaction.response.send_message(f"Loading selected...", ephemeral=True, delete_after=1)
        for value in select.values:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="More", url=implantData[value]["url"], style=discord.ButtonStyle.link))
            embed = discord.Embed(title=value, color=discord.Color.blurple())
            embed.description = implantData[value]["description"]
            embed.set_image(url=implantData[value]["image"])
            await interaction.followup.send(embed=embed, view=view)
class ImHelpView1(discord.ui.View): # yes, discord is that stupid and wont allow more than 25 options and yes it has to be defiend beforehand. If someone wants to make it prettier, please. i couldnt find a way.
    @discord.ui.select(
        placeholder = "Select implants youd like to view",
        min_values = 1,
        max_values = len(generate_options(1)),
        options = generate_options(1)
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.select):
        select.disabled = True
        await interaction.response.send_message(f"Loading selected...", ephemeral=True, delete_after=1)
        for value in select.values:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="More", url=implantData[value]["url"], style=discord.ButtonStyle.link))
            embed = discord.Embed(title=value, color=discord.Color.blurple())
            embed.description = implantData[value]["description"]
            embed.set_image(url=implantData[value]["image"])
            await interaction.followup.send(embed=embed, view=view)

@bot.tree.command(name="imhelp")
async def imhelp(interaction: discord.Interaction):
    await interaction.response.send_message("Select of which youd like to view information", view=ImHelpView(), ephemeral=True)
    await interaction.followup.send("Select of which youd like to view information", view=ImHelpView1(), ephemeral=True)

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

# Role management
@bot.tree.command(name="role")
@discord.app_commands.describe(role = "The role to manage")
@discord.app_commands.describe(user = "The user to manage the role for")
@discord.app_commands.describe(remove = "Remove the role")
async def role(interaction: discord.Interaction, role: discord.Role, user: discord.Member, remove: bool = False):
    role_management = config["role_management"]
    
    # Find target role in config
    found_role_config = None
    found_manager_roles = []
    found_group_role = None
    found_group_name = None
    group_roles = set()  # Track all roles in the group
    
    # Recursively search role configuration
    def find_role_in_config(config_section, parent_role_id=None):
        nonlocal found_role_config, found_manager_roles, group_roles
        
        # Add any role_id to group_roles if we have a parent
        if "role_id" in config_section and parent_role_id:
            group_roles.add(str(config_section["role_id"]))
            
        if "role_id" in config_section and str(config_section["role_id"]) == str(role.id):
            found_role_config = config_section
            return True
        
        for key, value in config_section.items():
            if isinstance(value, dict):
                if "manages" in value:
                    manager_role_id = value["role_id"]
                    for managed_role in value["manages"].values():
                        if "role_id" in managed_role:
                            group_roles.add(str(managed_role["role_id"]))
                        if str(managed_role["role_id"]) == str(role.id):
                            found_role_config = managed_role
                            found_manager_roles.append(manager_role_id)
                            return True
                if find_role_in_config(value, parent_role_id=config_section.get("role_id")):
                    return True
        return False

    # Search for the role in config
    for group_name, group_config in role_management.items():
        group_roles.clear()  # Reset for each group
        if find_role_in_config(group_config):
            found_group_role = group_config.get("role_id")
            found_group_name = group_name
            break
    
    if not found_role_config:
        await interaction.response.send_message("Role not managed", ephemeral=True)
        return
        
    # Permission check remains the same
    has_permission = False
    for manager_role_id in found_manager_roles:
        if discord.utils.get(interaction.user.roles, id=int(manager_role_id)):
            has_permission = True
            break
            
    if not has_permission:
        await interaction.response.send_message("You don't have permission to manage this role", ephemeral=True)
        return
        
    try:
        if remove:
            await user.remove_roles(role)
            if found_group_role:
                group_role = interaction.guild.get_role(int(found_group_role))
                if group_role:
                    # Check if user has any other roles from this group
                    has_other_roles = False
                    user_role_ids = [str(r.id) for r in user.roles]
                    for group_role_id in group_roles:
                        if group_role_id in user_role_ids and group_role_id != str(role.id):
                            has_other_roles = True
                            break
                            
                    if not has_other_roles:
                        await user.remove_roles(group_role)
                        
            await interaction.response.send_message(f"Removed role {role.name} from {user.display_name}", ephemeral=True)
        else:
            await user.add_roles(role)
            if found_group_role:
                group_role = interaction.guild.get_role(int(found_group_role))
                if group_role:
                    await user.add_roles(group_role)
            await interaction.response.send_message(f"Added role {role.name} to {user.display_name}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to modify roles", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

@tasks.loop(hours=1)  
async def update_OC_rankings():
    url = 'https://api.opencollective.com/graphql/v2'
    headers = {'Content-Type': 'application/json'}
    query = """
    {
        "query": "query account($slug:String){account(slug:$slug){name slug transactions(type:CREDIT){totalCount nodes{type fromAccount{name}amount{value}}}}}", 
        "variables": {"slug": "%s"}
    }
    """ % config["oc_slug"]
    
    try:
        response = requests.post(url, headers=headers, data=query)
        data = response.json()
        contributors = {}

        # Aggregate contributions 
        for node in data["data"]["account"]["transactions"]["nodes"]:
            name = node["fromAccount"]["name"]
            amount = node["amount"]["value"]  
            contributors[name] = contributors.get(name, 0) + amount

        # Sort contributors by amount
        sorted_contributors = sorted(contributors.items(), key=lambda x: x[1], reverse=True)
        sorted_contributors = sorted_contributors[:5]

        # Get guild
        for guild in bot.guilds:
            # Find or create OC category
            oc_category = discord.utils.get(guild.categories, name="OC contributors")
            if not oc_category:
                oc_category = await guild.create_category(
                    "OC contributors",
                    position=0, 
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(
                            send_messages=False,
                            add_reactions=False
                        )
                    }
                )

            existing_channels = {c.name: c for c in oc_category.channels}
            new_channels = set()

            # Create/update channels for top contributors
            for position, (name, amount) in enumerate(sorted_contributors):
                channel_name = f"{name}-{amount}".lower()
                channel_name = ''.join(c for c in channel_name if c.isalnum() or c in '-_') + "€"
                new_channels.add(channel_name)

                channel = existing_channels.get(channel_name)
                if not channel:
                    channel = await oc_category.create_text_channel(
                        channel_name,
                        position=position,  # Set initial position
                        overwrites={
                            guild.default_role: discord.PermissionOverwrite(
                                send_messages=False,
                                add_reactions=False
                            )
                        }
                    )
                else:
                    # Move existing channel to correct position
                    await channel.move(position=position, category=oc_category)

            # Remove old contributor channels
            for old_channel_name in existing_channels.keys() - new_channels:
                channel = existing_channels[old_channel_name]
                await channel.delete()

    except Exception as e:
        print(f"Failed to update OC rankings: {e}")

bot.run(os.getenv("DISCORD_TOKEN"))