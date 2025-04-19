import discord
from discord.ext import commands
from configman import config
from discord import app_commands
import logging


class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Role management
    @app_commands.command(name="role")
    @discord.app_commands.describe(role="The role to manage")
    @discord.app_commands.describe(user="The user to manage the role for")
    @discord.app_commands.describe(remove="Remove the role")
    async def role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        user: discord.Member,
        remove: bool = False,
    ):
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

            if "role_id" in config_section and str(config_section["role_id"]) == str(
                role.id
            ):
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
                    if find_role_in_config(
                        value, parent_role_id=config_section.get("role_id")
                    ):
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
            await interaction.response.send_message(
                "You don't have permission to manage this role", ephemeral=True
            )
            logging.info(
                f"User {interaction.user.name} doesn't have permission to manage role {role.name}"
            )
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
                            if group_role_id in user_role_ids and group_role_id != str(
                                role.id
                            ):
                                has_other_roles = True
                                break

                        if not has_other_roles:
                            await user.remove_roles(group_role)

                await interaction.response.send_message(
                    f"Removed role {role.name} from {user.display_name}", ephemeral=True
                )
                logging.info(f"Role {role.name} removed from {user.name}")
            else:
                await user.add_roles(role)
                if found_group_role:
                    group_role = interaction.guild.get_role(int(found_group_role))
                    if group_role:
                        await user.add_roles(group_role)
                await interaction.response.send_message(
                    f"Added role {role.name} to {user.display_name}", ephemeral=True
                )
                logging.info(f"Role {role.name} added to {user.name}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to modify roles", ephemeral=True
            )
            logging.info(
                f"Missing permissions to manage role {role.name} for {user.name}"
            )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred: {str(e)}", ephemeral=True
            )
            logging.exception(
                f"An error occurred while managing roles for {user.name}: {str(e)}"
            )


async def setup(bot):
    await bot.add_cog(RoleManagement(bot))
    logging.info("RoleManagement cog loaded")
