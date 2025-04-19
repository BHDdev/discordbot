import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import logging
from configman import config


class PurelyMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def domain_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=domain, value=domain)
            for domain in config["purelymail"]["domains"]
            if current.lower() in domain.lower()
        ]

    @app_commands.command(name="register")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.autocomplete(domain=domain_autocomplete)
    async def register(
        self,
        interaction: discord.Interaction,
        username: str,
        domain: str,
        password: str,
        recovery_email: str,
        enable_search_indexing: bool = True,
        send_welcome_email: bool = True,
        enable_password_reset: bool = True,
    ):

        # Acknowledge the interaction first
        await interaction.response.defer(ephemeral=True)

        if domain not in config["purelymail"]["domains"]:
            await interaction.response.send_message(
                "Invalid domain selected. Please choose from the provided options.",
                ephemeral=True,
            )
            return

        # Prepare the API request
        url = "https://purelymail.com/api/v0/createUser"
        headers = {
            "accept": "application/json",
            "Purelymail-Api-Token": config["purelymail"]["api_token"],
            "Content-Type": "application/json",
        }

        # Prepare the request body
        payload = {
            "userName": username,
            "domainName": domain,
            "password": password,
            "enablePasswordReset": enable_password_reset,
            "recoveryEmail": recovery_email,
            "enableSearchIndexing": enable_search_indexing,
            "sendWelcomeEmail": send_welcome_email,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["type"] == "error":
                            await interaction.followup.send(
                                f"Failed to create email account. Error: {data['message']}",
                                ephemeral=True,
                            )
                        else:
                            await interaction.followup.send(
                                f"Successfully created email account: {username}@{domain} {data}",
                                ephemeral=True,
                            )
                    else:
                        error_text = await response.text()
                        await interaction.followup.send(
                            f"Failed to create email account. Error: {error_text}",
                            ephemeral=True,
                        )
        except Exception as e:
            await interaction.followup.send(
                f"An error occurred: {str(e)}", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(PurelyMail(bot))
    logging.info("PurelyMail cog loaded")
