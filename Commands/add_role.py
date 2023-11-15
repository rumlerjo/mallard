from interactions import Extension, Client, SlashContext, slash_command, SlashCommandOption, OptionType, Permissions, Role, ChannelType
from bot import Bot
from Utilities.enums import CommandEnums, CooldownEnums
from typing import Optional

class AddRole(Extension):
    def __init__(self, client: Client) -> None:
        self.client = client
        self._parent: Bot = None

    @slash_command(
        name = "admin",
        sub_cmd_name = "add-role",
        sub_cmd_description = "Add a role from this server to be self-assignable.",
        default_member_permissions = Permissions.ADMINISTRATOR | Permissions.MANAGE_ROLES,
        dm_permission = False,
        options = [
            SlashCommandOption(
                name = "role",
                description = "The role to make self-assignable.",
                required = True,
                type = OptionType.ROLE
            ),
            SlashCommandOption(
                name = "descr",
                description = "A short description of the role.",
                required = False,
                type = OptionType.STRING
            )
        ]
    )
    async def add_role(self, ctx: SlashContext, role: Role, descr: Optional[str] = "") -> None:
        await self._parent.sql.setup_bot_info(ctx)

        cooldown = self._parent.get_cooldown(ctx.user.id, CommandEnums.ADD_REACTION)
        if cooldown:
            await ctx.send("You are on cooldown for this command for another " + str(cooldown) + " seconds.",
            ephemeral = True)
            return
        
        self._parent.sql.add_assignable_guild_role(int(ctx.guild_id), int(role.id), role.name, descr = descr)

        await ctx.send(f"Role {role.name} added to self-assignment.", ephemeral=True)
        self._parent.set_cooldown(CooldownEnums.GLOBAL, CommandEnums.ADD_REACTION, ctx.user.id, 5)
        
    def add_parent(self, parent: Bot) -> None:
        self._parent = parent

    def __str__(self) -> str:
        return "Add role: allows server admins to make roles self-assignable."

    def __repr__(self) -> str:
        return str(self)

def setup(client: Client):
    return AddRole(client)