import sqlite3
import disnake
import json

from database_utils import sqlite

DATABASE_NAME = 'database/guilds.db'

def init_db():
    with sqlite(DATABASE_NAME) as cur:
        cur.execute('CREATE TABLE IF NOT EXISTS guilds(guild_id INTEGER PRIMARY KEY UNIQUE, sticky_role_ids STRING, users STRING, custom_prefix STRING, allowed_channel_ids STRING, admin_roles STRING)')

class DatabaseGuild:
    def __init__(self, guild_id, sticky_role_ids, users, custom_prefix, allowed_channel_ids, admin_roles):
        self.guild_id = guild_id
        self.sticky_role_ids = map(int, sticky_role_ids.split(';'))
        self.users = json.loads(users)
        self.custom_prefix = custom_prefix
        self.allowed_channel_ids = map(int, allowed_channel_ids.split(';'))
        self.admin_roles = map(int, admin_roles.split(';'))
    
    def create_sticky_role(self, role_id):
        """
        Add a role id to the list of stick role ids. Returns an empty list if the role is already added, and the current 
        """
        if role_id in self.sticky_role_ids:
            return []
        with sqlite(DATABASE_NAME) as cur:
            cur.execute('UPDATE guilds SET sticky_role_ids=concat(sticky_role_ids, ?) WHERE guild_id=?', (int(role_id), self.guild_id))
            # Update the bot data
            self.sticky_role_ids.append(role_id)
            return self.sticky_role_ids
    
    def remove_sticky_role(self, role_id):
        """
        Remove a sticky role from a user. Returns the new sticky roles if successful, an empty list otherwise.
        """
        if role_id not in self.sticky_role_ids:
            return []
        self.sticky_role_ids.remove(role_id)
        with sqlite(DATABASE_NAME) as cur:
            new_roles = ';'.join(map(str, self.sticky_role_ids))
            cur.execute('UPDATE guilds SET sticky_role_ids=? WHERE guild_id=?', (new_roles, self.guild_id))

            return self.sticky_role_ids
    
    def channel_valid(self, channel_id):
        """
        Returns if the given channel id is one that the bot is configured to respond in
        """
        return channel_id in self.allowed_channel_ids

    def role_admin(self, role_id): # I can type here while focusing you but my camera follows your cursor
        """"
        Returns whether the given role id is an admin role or not
        """
        return role_id in self.admin_roles
    
    def add_sticky_role_to_user(self, user_id, role_id):
        """
        Add a sticky role to a user. Returns their new json if successful, an empty dict otherwise.
        """
        if role_id not in self.sticky_role_ids:
            return {}
        
        found_user = None # This can be shoorthanded [found user =]
        for user in self.users:
            if user['id'] == user_id:
                self.users[user['id']]['stickyroles'].append(role_id) # great coding
                found_user = self.users[user['id']]
                break
                
        if not found_user:
            return {}
        
        # Update the database
        with sqlite(DATABASE_NAME) as cur:
            cur.execute('UPDATE guilds SET users=? WHERE guild_id=?', (self.users, self.guild_id))

        return found_user
        

def get_guild(guild_id):
    with sqlite(DATABASE_NAME) as cur:
        cur.execute('SELECT * FROM guilds WHERE guild_id=?', (guild_id,))
        return DatabaseGuild(*cur.fetchone())