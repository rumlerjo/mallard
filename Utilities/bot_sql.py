from sqlite3 import Connection
from interactions import SlashContext, Permissions
from Utilities.enums import UserType
from typing import Tuple, List, Optional

class BotSQL:
    def __init__(self, connection: Connection) -> None:
        self.conn = connection

    def execute_and_commit(self, queryString: str) -> None:
        """
        Executes and commits a query. For use when data will change. (ex: insertion, deletion)
        :return: None
        """
        try:
            self.conn.execute(queryString)
            self.conn.commit()
        except:
            return

    def execute_selection(self, queryString: str) -> List[Tuple]:
        """
        Make a selection query
        :return: List of data selected, will usually be in tuple form.
        """
        try:
            selectionCursor = self.conn.execute(queryString)
            return selectionCursor.fetchall()
        except:
            return
    
    async def derive_user_permissions(self, ctx: SlashContext) -> int:
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
    
    def get_user(self, userId: int) -> Optional[List[Tuple]]:
        return self.execute_selection(f"SELECT * FROM users WHERE user_id = {int(userId)};")
    
    def get_guild_user(self, guildId: int, userId: int) -> Optional[List[Tuple]]:
        return self.execute_selection(f"SELECT * FROM guild_users WHERE guild_id = {guildId} AND user_id = {userId};")
    
    def get_guild(self, guildId: int) -> Optional[List[Tuple]]:
        return self.execute_selection(f"SELECT * from guilds WHERE guild_id = {guildId};")
            
    async def setup_user(self, ctx: SlashContext) -> None:
        """
        Create the bot user in the database. Creates both guild and global user.
        :param ctx: Event context from Discord
        :return: none
        """
        if ctx.user:
            user = self.get_user(int(ctx.user.id))
            guild_user = self.get_guild_user(int(ctx.guild_id), int(ctx.user.id))
            
            if not user:
                self.execute_and_commit(f"""
                                                INSERT OR REPLACE INTO users(user_id)
                                                VALUES({int(ctx.user.id)});
                                            """)
            if not guild_user:
                self.execute_and_commit(f"""
                                            INSERT OR REPLACE INTO guild_users(user_id, guild_id, permissions)
                                            VALUES({int(ctx.user.id)}, {int(ctx.guild_id)}, {await self.derive_user_permissions(ctx)});
                                        """)
    
    async def setup_guild(self, ctx: SlashContext):
        if ctx.guild:
            guild = self.get_guild(int(ctx.guild_id))

            if not guild:
                self.execute_and_commit(f"INSERT OR REPLACE INTO guilds(guild_id) VALUES({int(ctx.guild_id)})")
    
    async def setup_bot_info(self, ctx: SlashContext) -> None:
        await self.setup_guild(ctx)
        await self.setup_user(ctx)
        
    async def get_guild_user_permissions(self, guildId: int, userId: int) -> Optional[int]:
        """
        Get a guild user's permission level
        :param guildId: The guild ID of the user as an integer
        :param userId: The user ID as an integer
        :return: Permission level as integer or None
        """
        permissions = self.execute_selection(f"SELECT permissions FROM guild_users WHERE \
                                               guild_id = {guildId} AND user_id = {userId};")
        
        return permissions[0][0] if permissions else None
    
    def get_assignable_guild_roles(self, guildId: int) -> List[Tuple[int, str, str]]:
        return self.execute_selection(
                        f"""
                            SELECT 
                                role_id,
                                role_name,
                                descr
                            FROM role_reactions
                            WHERE guild_id = {guildId};
                        """
                    )
        
    def add_assignable_guild_role(self, guildId: int, roleId: int, roleName: str, descr: str = "") -> None:
        self.execute_and_commit(
            f"""
                INSERT OR REPLACE INTO
                  role_reactions(role_id, guild_id, role_name, descr)
                VALUES({roleId}, {guildId}, '{roleName}', '{descr}');
             """
        )
    