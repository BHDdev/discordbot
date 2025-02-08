import discord
from discord.ext import commands
from discord import app_commands
import logging


class MoveMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="move")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def move(
        self,
        interaction: discord.Interaction,
        number: int,
        channel: discord.TextChannel,
    ):
        try:
            # Validate input
            if number <= 0:
                await interaction.response.send_message(
                    "Please provide a positive number of messages to move.",
                    ephemeral=True,
                )
                return

            # Defer the response since this might take a while
            await interaction.response.defer(ephemeral=True)

            # Get messages
            messages = []
            async for msg in interaction.channel.history(limit=number):
                messages.append(msg)

            messages.reverse()  # Process oldest messages first

            for message in messages:
                # Create webhook
                webhook = await channel.create_webhook(name=message.author.display_name)

                try:
                    # Prepare files if any attachments exist
                    files = [
                        await attachment.to_file() for attachment in message.attachments
                    ]

                    # Get avatar URL with proper fallback
                    avatar_url = (
                        message.author.display_avatar.url
                        if message.author.avatar
                        else message.author.default_avatar.url
                    )

                    # Send message through webhook
                    await webhook.send(
                        content=message.content,
                        username=message.author.display_name,
                        avatar_url=avatar_url,
                        files=files,
                    )

                    # delete original message
                    await message.delete()
                finally:
                    # Always cleanup the webhook
                    await webhook.delete()

            await interaction.followup.send(
                f"Successfully moved {len(messages)} messages to {channel.mention}",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "I don't have the required permissions to perform this action.",
                ephemeral=True,
            )
        except Exception as e:
            logging.error(f"Error in move command: {str(e)}")
            await interaction.followup.send(
                "An error occurred while moving messages.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(MoveMessages(bot))
    logging.info("MoveMessages cog loaded")
