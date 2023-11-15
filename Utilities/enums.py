"""
Enumerations for various bot functions
@author John Rumler https://github.com/rumlerjo
"""

from enum import Enum

class CooldownEnums(Enum):
    """Enumerations of cooldown types"""
    GUILD = 1
    GLOBAL = 2

class CommandEnums(Enum):
    """Enumerations of commands"""
    PING = 1
    RELOAD = 2
    CREATE_REACTION = 3
    ADD_REACTION = 4

class UserType(Enum):
    NORMAL = 1
    BOT_ADMIN = 2
    GUILD_ADMIN = 3
    DEVELOPER = 4
