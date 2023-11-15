"""
Repurposed from another project
An implementation of a wrapper of core bot features
Authored by John Rumler/rumlerjo
"""

import interactions
from os import scandir
from typing import TypeVar, Set, Optional, Union, List, Any, Tuple
from Utilities.cooldown import CooldownManager
from interactions import Extension, Snowflake, SlashContext, Permissions
from sqlite3 import Connection
from Utilities.enums import UserType
from Utilities.bot_sql import BotSQL


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
    def __init__(self, client: interactions.Client, dbConn: Connection) -> None:
        self._client = client
        self._cooldowns = CooldownManager()
        self.sql = BotSQL(dbConn)

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
        
    def _create_database_tables(self) -> None:
        """
        Read in and execute database creation scripts on startup
        :return None:
        """
        for queryFile in get_database_paths():
            fp = open(queryFile, "r")
            fpData = fp.read()
            self.sql.execute_and_commit(fpData)
            fp.close()