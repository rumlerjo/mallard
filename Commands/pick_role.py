from interactions import Extension, Client, Permissions, CommandType, ComponentContext, SlashContext, slash_command, component_callback, StringSelectMenu, StringSelectOption, Embed, Color, Button, ButtonStyle, spread_to_rows
from time import time
from bot import Bot
from Utilities.enums import CommandEnums, CooldownEnums
from typing import Tuple, List, Dict, Any, Union, Optional
import json

class PickRole(Extension):
    def __init__(self, client: Client) -> None:
        self.client = client
        self._parent: Bot = None
        self.guildSelections: Dict[str, Tuple[List[Tuple[int, str]], float]] = dict()
        self.selectionTracker: Dict[str, Tuple(int, str, str)] = dict()

    def _make_embed(self, ctx: Union[SlashContext, ComponentContext], roleName: Optional[str] = None, \
                    roleDesc: Optional[str] = None, applied: bool = False):
        embed = Embed()
        embed.color = Color().random()
        embed.title = "Pick a role"
        if roleName and not applied:
            embed.add_field(name="Role name", value=roleName)
            embed.add_field(name="Description", value=roleDesc if roleDesc and roleDesc != "" else "No description.")
        else:
            embed.add_field(name="Role picker", value="Select a role from the dropdown and click 'Apply' to be given that role.")
            if applied:
                embed.add_field(name="Last applied role", value=roleName)
        embed.set_footer(text="Interaction available for: " + ctx.user.username, icon_url=ctx.user.avatar_url)
        return embed
    
    def _get_role_data(self, ctx: Union[SlashContext, ComponentContext]) -> List[Tuple[int, str, str]]:
        roleData: List[Tuple[int, str, str]] = list()

        # cache and re-grab every 10 seconds
        if self.guildSelections.get(ctx.guild_id):
            data, last = self.guildSelections.get(ctx.guild_id)
            if time() - last >= 10:
                roleData = self._parent.sql.get_assignable_guild_roles(int(ctx.guild_id))
                self.guildSelections[ctx.guild_id] = (roleData, time())
            else:
                roleData = data
        else:
            roleData = self._parent.sql.get_assignable_guild_roles(int(ctx.guild_id))

        return roleData
    
    async def _get_filtered_role_data(self, ctx: Union[SlashContext, ComponentContext]) -> List[Tuple[int, str, str]]:
        roleData = self._get_role_data(ctx)
        filteredData: List[Tuple[int, str, str]] = list()
        userMember = await ctx.guild.fetch_member(ctx.user.id)
        # using a dict for O(1) accesses, only O(n) instantiation keeping this from O(n^2)
        userRoles = {str(role.id): True for role in userMember.roles}
        for role in roleData:
            if str(role[0]) not in userRoles:
                filteredData.append(role)
        
        return filteredData


    @slash_command(
        name = "role",
        sub_cmd_name = "list",
        sub_cmd_description = "Display a list of roles available to pick from.",
        dm_permission = False,
    )
    async def pick_role(self, ctx: SlashContext) -> None:
        await self._parent.sql.setup_bot_info(ctx)

        cooldown = self._parent.get_cooldown(ctx.user.id, CommandEnums.PICK_ROLE)
        if cooldown:
            await ctx.send("You are on cooldown for this command for another " + str(cooldown) + " seconds.",
            ephemeral = True)
            return
        
        roleData = await self._get_filtered_role_data(ctx)

        if len(roleData) < 1:
            await ctx.send("No roles are available for self-assignment.", ephemeral=True)
            return

        selectMenu = StringSelectMenu(
            [
                StringSelectOption(
                    label = roleName,
                    value = json.dumps([role, roleName, descr])
                ) for role, roleName, descr in roleData
            ],
            custom_id = "SelectRole",
            placeholder = "Select a role...",
        )

        await ctx.send(embed=self._make_embed(ctx), ephemeral=True, components = selectMenu)
        self._parent.set_cooldown(CooldownEnums.GLOBAL, CommandEnums.PICK_ROLE, ctx.user.id, 5)

    @component_callback("SelectRole")
    async def select_role(self, ctx: ComponentContext) -> None:
        roleId, roleName, roleDescr = json.loads(ctx.values[0])
        self.selectionTracker[ctx.user.id] = (roleId, roleName, roleDescr)

        applyButton = Button(
            custom_id = "ApplyRole",
            style = ButtonStyle.GREEN,
            label = "Apply"
        )

        componentRow = spread_to_rows(ctx.component, applyButton, max_in_row=2)

        await ctx.edit_origin(embed=self._make_embed(ctx, roleName, roleDescr), components=componentRow)

    @component_callback("ApplyRole")
    async def apply_role(self, ctx: ComponentContext) -> None:
        roleId, roleName, roleDescr = int(), str(), str()

        if self.selectionTracker.get(ctx.user.id):
            roleId, roleName, roleDescr = self.selectionTracker.get(ctx.user.id)
        else:
            await ctx.edit_origin(content="Something went wrong.", embed=None, components=None)
            return
        
        await ctx.member.add_role(roleId)
        
        self.selectionTracker.pop(ctx.user.id)
        
        roleData = await self._get_filtered_role_data(ctx)

        if len(roleData) < 1:
            message_id = ctx.message_id
            await ctx.send(content="No more roles are available for self-assignment.", ephemeral=True)
            await ctx.delete(message_id)
            return

        selectMenu = StringSelectMenu(
            [
                StringSelectOption(
                    label = roleName,
                    value = json.dumps([role, roleName, descr])
                ) for role, roleName, descr in roleData
            ],
            custom_id = "SelectRole",
            placeholder = "Select a role...",
        )

        await ctx.edit_origin(embed=self._make_embed(ctx, roleName, applied=True), components=selectMenu)


        
    def add_parent(self, parent: Bot) -> None:
        self._parent = parent

    def __str__(self) -> str:
        return "Pick Role command: Allows a server administrator to create a role picking dialog."

    def __repr__(self) -> str:
        return str(self)

def setup(client: Client):
    return PickRole(client)