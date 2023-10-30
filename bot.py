"""
Repurposed from another project
An implementation of a wrapper of core bot features
Authored by John Rumler/rumlerjo
"""

import interactions
from os import scandir
from typing import TypeVar, Set, Optional, Union, List, Any, Tuple
from lib.cooldown import CooldownManager
from interactions import Extension, Snowflake, SlashContext, Permissions
from sqlite3 import Connection, Cursor
from Utilities.enums import UserType


# A generic class
T = TypeVar("T")
# Forward declaration of Bot
Bot = TypeVar("Bot")

class BotExtension(Extension):
    """
    A template class used for typehinting
    """
    def add_parent(self, parent: Bot) -> None:
        pass

def get_command_paths() -> Set[T]:
    """
    Gets all names of extensions to load onto the client
    :return: Set of all extension names
    """
    paths = set()
    for file in scandir("./Commands"):
        if file.is_file and file.name.find(".py") != -1:
            command_name = file.name.replace(".py", "")
            paths.add(f"Commands.{command_name}")
    return paths

def get_database_paths() -> Set[T]:
    paths = set()
    for file in scandir("./DatabaseQueries/CreateTables"):
        if file.is_file and file.name.find(".sql") != -1:
            paths.add("./DatabaseQueries/CreateTables/" + file.name)
    return paths

class Bot:
    """
    Wrapper for the bot and some of its functions.
    """
    def __init__(self, client: interactions.Client, dbCursor: Connection) -> None:
        self._client = client
        self._cooldowns = CooldownManager()
        self._db = dbCursor

        # used as a checker to see which commands are running
        self._extensions: Set[Extension] = set()

        # load our commands and register discord events
        self.load_commands()
        self.register_events()

        # setup database tables
        self._create_database_tables()

    def load_commands(self) -> None:
        """
        Load commands onto the client
        :return: None
        """
        for command in get_command_paths():
            self._client.load_extension(command)
            extensions: List[BotExtension] = self._client.get_extensions(command)
            # looping as a precaution however this should only return 1.
            for extension in extensions:
                self._extensions.add(extension) # this is now not necessary. may remove
                extension.add_parent(self)
    
    def register_events(self) -> None:
        """
        Register discord gateway events
        :return: None
        """
        @self._client.event(event_name="on_ready")
        async def __ready():
            print("started bot")

    async def reload_commands(self) -> None:
        """
        Reload commands on the client
        :return: None
        """
        for command in get_command_paths():
            self._client.reload_extension(command)
            extensions: List[BotExtension] = self._client.get_extensions(command)
            for extension in extensions:
                self._extensions.add(extension)
                extension.add_parent(self)

    async def unload_all_commands(self) -> None:
        """
        Unload all currently loaded commands
        :return None:
        """
        for command in get_command_paths():
            self._client.unload_extension(command)
        # just set it back to empty because it (should) be
        self._extensions = set()

    async def unload_and_reload_commands(self) -> None:
        """
        Fully unload and reload every currently loaded extension
        :return None:
        """
        self.unload_all_commands()
        self.load_commands()

    def set_cooldown(self, cType: int, commandId: int, userId: Union[str, int],
    time: int, guildId: Optional[Union[str, int]] = None) -> None:
        """
        A wrapper for CooldownManager's set_cooldown
        :param cType: Enumeration of cooldown type
        :param commandId: Command enumeration
        :param userId: Integer or String representation of a user's unique identifier
        :param time: Amound of time in seconds to timeout command
        :param guildId: Integer or String representation of a guild's unique identifier
        :return: None
        """
        self._cooldowns.set_cooldown(commandId, userId, time, cType, guildId)

    def get_cooldown(self, userId: Snowflake, commandId: int,
    guildId: Optional[Snowflake] = None) -> Optional[int]:
        """
        A wrapper for CooldownManager's get_cooldown
        :param userId: Integer or String representation of a user's unique identifier
        :param commandId: Command enumeration
        :param guildId: Integer or String representation of a guild's unique identifier
        :return: Amount of time left in cooldown or None
        """
        return self._cooldowns.get_cooldown(userId, commandId, guildId)
    
    def execute_and_commit(self, queryString: str) -> None:
        """
        Executes and commits a query. For use when data will change. (ex: insertion, deletion)
        :return: None
        """
        try:
            self._db.execute(queryString)
            self._db.commit()
        except:
            return

    def execute_selection(self, queryString: str) -> List[Tuple]:
        """
        Make a selection query
        :return: List of data selected, will usually be in tuple form.
        """
        try:
            selectionCursor = self._db.execute(queryString)
            return selectionCursor.fetchall()
        except:
            return
        
    async def _derive_user_permissions(self, ctx: SlashContext) -> int:
        perms = UserType.NORMAL.value
        guildOwner = await ctx.guild.fetch_owner()
        if str(ctx.user.id) == "311663246622982145":
            perms = UserType.DEVELOPER.value
        elif ctx.user.id == guildOwner.id:
            perms = UserType.GUILD_ADMIN.value
        else:
            userMember = await ctx.guild.fetch_member(ctx.user.id)
            userRoles = userMember.roles
            for role in userRoles:
                isAdmin = (role.permissions & Permissions.ADMINISTRATOR) == Permissions.ADMINISTRATOR
                if isAdmin:
                    perms = UserType.GUILD_ADMIN.value
                    break
        return perms
                
        
    def _create_database_tables(self):
        for queryFile in get_database_paths():
            fp = open(queryFile, "r")
            fpData = fp.read()
            self.execute_and_commit(fpData)
            fp.close()

    async def _confirm_guild(self, ctx: SlashContext) -> bool:
        if not ctx.guild:
            await ctx.send("Sorry! Commands are not currently supported outside of guild contexts.", ephemeral=True)
            return False
        return True
            
    async def _setup_user(self, ctx: SlashContext):

        self.execute_and_commit(f"""
                                    INSERT OR REPLACE INTO users(user_id)
                                    VALUES({int(ctx.user.id)});
                                    """)
        
        self.execute_and_commit(f"""
                                    INSERT OR REPLACE INTO guild_users(user_id, guild_id, permissions)
                                    VALUES({int(ctx.user.id)}, {int(ctx.guild_id)}, {await self._derive_user_permissions(ctx)});
                                    """)

    async def command_checks(self, ctx: SlashContext) -> bool:
        isValid = await self._confirm_guild(ctx)
        if isValid:
            await self._setup_user(ctx)
            return True
        return False