import discord
from discord.ext import tasks, commands
import aiohttp
from configman import config
import logging


class OCLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_OC_rankings.start()

    @tasks.loop(hours=2)
    async def update_OC_rankings(self):
        url = "https://api.opencollective.com/graphql/v2"
        headers = {"Content-Type": "application/json"}
        query = (
            """
        {
            "query": "query account($slug:String){account(slug:$slug){name slug transactions(type:CREDIT){totalCount nodes{type fromAccount{name}amount{value}}}}}", 
            "variables": {"slug": "%s"}
        }
        """
            % config["oc_slug"]
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=query) as response:
                    data = await response.json()
            # response = requests.post(url, headers=headers, data=query)
            # data = response.json()
            contributors = {}

            # Aggregate contributions
            for node in data["data"]["account"]["transactions"]["nodes"]:
                name = node["fromAccount"]["name"]
                amount = node["amount"]["value"]
                contributors[name] = contributors.get(name, 0) + amount

            # Sort contributors by amount
            sorted_contributors = sorted(
                contributors.items(), key=lambda x: x[1], reverse=True
            )
            sorted_contributors = sorted_contributors[:5]

            # Get guild
            for guild in self.bot.guilds:
                # Find or create OC category
                oc_category = discord.utils.get(
                    guild.categories, name="OC contributors"
                )
                if not oc_category:
                    oc_category = await guild.create_category(
                        "OC contributors",
                        position=0,
                        overwrites={
                            guild.default_role: discord.PermissionOverwrite(
                                send_messages=False, add_reactions=False
                            )
                        },
                    )

                existing_channels = {c.name: c for c in oc_category.channels}
                new_channels = set()

                # Create/update channels for top contributors
                for position, (name, amount) in enumerate(sorted_contributors):
                    channel_name = f"{name}-{amount}".lower()
                    channel_name = (
                        "".join(c for c in channel_name if c.isalnum() or c in "-_")
                        + "€"
                    )
                    new_channels.add(channel_name)

                    channel = existing_channels.get(channel_name)
                    if not channel:
                        channel = await oc_category.create_text_channel(
                            channel_name,
                            position=position,  # Set initial position
                            overwrites={
                                guild.default_role: discord.PermissionOverwrite(
                                    send_messages=False, add_reactions=False
                                )
                            },
                        )
                    else:
                        # Move existing channel to correct position
                        await channel.move(position=position, category=oc_category)

                # Remove old contributor channels
                for old_channel_name in existing_channels.keys() - new_channels:
                    channel = existing_channels[old_channel_name]
                    await channel.delete()

        except Exception as e:
            # print(f"Failed to update OC rankings: {e}")
            logging.exception(f"Failed to update OC rankings: {e}")


async def setup(bot):
    await bot.add_cog(OCLeaderboard(bot))
    logging.info("OCLeaderboard cog loaded")
