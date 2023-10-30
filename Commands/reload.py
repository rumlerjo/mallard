from interactions import SlashContext, Extension, Client, slash_command
from bot import Bot
from Utilities.enums import UserType

# will need to lock down to only me being able to use this

class Reload(Extension):
    def __init__(self, client: Client) -> None:
        self.client = client
        self._parent: Bot = None

    @slash_command(
        name = "reload", 
        description = "Reload currently active commands 🔄 (Dev Tool)",
    )
    async def reload(self, ctx: SlashContext) -> None:
        isValid = await self._parent.command_checks(ctx)
        if isValid:
            permissionsData = self._parent.execute_selection(f"SELECT permissions FROM guild_users WHERE \
                                                                guild_id = {int(ctx.guild_id)} AND user_id = {int(ctx.user.id)}")
            permissions: int
            if permissionsData:
                permissions = permissionsData[0][0]
            else:
                await ctx.send("Unable to load your user data.", ephemeral=True)
                return
            
            if permissions == UserType.DEVELOPER.value:
                await self._parent.reload_commands()
                await ctx.send("Reloaded Commands.", ephemeral=True)
            else:
                await ctx.send("Your permissions level is not high enough for this command.")
    
    def add_parent(self, parent: Bot) -> None:
        self._parent = parent

    def __str__(self) -> str:
        return "Reload command: reloads all currently active commands."

    def __repr__(self) -> str:
        return str(self)

def setup(client: Client):
    return Reload(client)