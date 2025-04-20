import discord
from discord.ext import commands
import logging


class GeneralPinning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        # print(f"{user} reacted with {reaction.emoji}")
        logging.debug(f"{user} reacted with {reaction.emoji}")
        if reaction.emoji == "📌" or reaction.emoji == "📍":
            if reaction.message.author.bot:
                return
            if "!NP!" in reaction.message.content:
                return
            pins = 0
            unpins = 0
            for reaction in reaction.message.reactions:
                if reaction.emoji == "📍":
                    unpins = reaction.count
                if reaction.emoji == "📌":
                    pins = reaction.count

            if pins > unpins + 4:
                logging.info(f"Pinning message {reaction.message.id}")
                logging.debug(f"Pins: {pins}, Unpins: {unpins}")
                await reaction.message.pin()
            elif unpins > pins + 4:
                logging.info(f"Unpinning message {reaction.message.id}")
                logging.debug(f"Pins: {pins}, Unpins: {unpins}")
                await reaction.message.unpin()


async def setup(bot):
    await bot.add_cog(GeneralPinning(bot))
    logging.info("GeneralPinning cog loaded")
