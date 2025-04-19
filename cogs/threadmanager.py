import discord
from discord.ext import commands
from configman import config
import logging


class ThreadManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Thread management commands
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
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

        if any(role.id == int(config["pinup_role_id"]) for role in user.roles):
            if reaction.emoji == "📌":
                # print("Pinning message")
                logging.info(f"Pinning message {reaction.message.id}")
                await reaction.message.pin()
            elif reaction.emoji == "📍":
                # print("Unpinning message")
                logging.info(f"Unpinning message {reaction.message.id}")
                await reaction.message.unpin()


async def setup(bot):
    await bot.add_cog(ThreadManager(bot))
    logging.info("ThreadManager cog loaded")
