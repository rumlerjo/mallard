from interactions import Extension, Client, Permissions, CommandType, SlashContext, slash_command
from bot import Bot
from Utilities.enums import CommandEnums, CooldownEnums

class PickRole(Extension):
    def __init__(self, client: Client) -> None:
        self.client = client
        self._parent: Bot = None

    @slash_command(
        name = "role", 
        description = "erm",
    )
    async def pick_role(self, ctx: SlashContext) -> None:
        cooldown = self._parent.get_cooldown(ctx.user.id, CommandEnums.CREATE_REACTION)
        if cooldown:
            await ctx.send("You are on cooldown for this command for another " + str(cooldown) + " seconds.",
            ephemeral = True)
            return
        await ctx.send("This is a Test!", ephemeral=True)
        self._parent.set_cooldown(CooldownEnums.GLOBAL, CommandEnums.CREATE_REACTION, ctx.user.id, 5)
        
    def add_parent(self, parent: Bot) -> None:
        self._parent = parent

    def __str__(self) -> str:
        return "Pick Role command: Allows a server administrator to create a role picking dialog."

    def __repr__(self) -> str:
        return str(self)

def setup(client: Client):
    return PickRole(client)