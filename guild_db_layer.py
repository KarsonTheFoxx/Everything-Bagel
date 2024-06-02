import sqlite3
import disnake
import json

from database_utils import sqlite

DATABASE_NAME = 'database/guilds.db'

def init_db():
    """
    Initialise the guild database
    """
    with sqlite(DATABASE_NAME) as cur:
        cur.execute('CREATE TABLE IF NOT EXISTS guilds(guild_id INTEGER PRIMARY KEY UNIQUE, ' \
                    'sticky_role_ids STRING, users STRING, custom_prefix STRING, ' \
                    'allowed_channel_ids STRING)')

class DatabaseGuild:
    def __init__(self, guild_id, sticky_role_ids, users, custom_prefix, allowed_channel_ids, admin_roles):
        self.guild_id = guild_id
        self.sticky_role_ids = map(int, sticky_role_ids.split(';'))
        self.users = json.loads(users)
        self.custom_prefix = custom_prefix
        self.allowed_channel_ids = map(int, allowed_channel_ids.split(';'))
        self.admin_roles = map(int, admin_roles.split(';'))
    
    def init_user(self, user_id):
        """
        Initialise a user into the users column if they have not been initialised yet. Returns True if they were initialised, 
            False otherwise (they already existed in the db.)
        Commonly run in add_sticky_role_to_user function to make user that a user can be accesssed.
        """
        # check if the user already exists
        for user in self.users:
            if user['id'] == user_id:
                return False
        
        # Initliase the user
        self.users.append({'id': user_id, 'sticky_roles':[]})

        # Update the database
        with sqlite(DATABASE_NAME) as cur:
            # Use json.dumps to get a string of the json data which the database can use
            cur.execute('UPDATE guilds SET users=? WHERE guild_id=?', (json.dumps(self.users), self.guild_id))
        
        return True # The user was initialised

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
        Add a sticky role to a user. Returns their new json if successful, an empty dict if the role isn't sticky.
        **THIS COMMANDS ASSUMES THE USER ID IS VALID AND WILL ALWAYS ADD IT TO THE DATABASE**
        """
        self.init_user(user_id) # Make sure the user is initialised in the database.
        if role_id not in self.sticky_role_ids:
            return {}
        
        found_user = None # This can be shoorthanded [found user =]
        # Iterate through users and find the correct id
        for user in self.users:
            if user['id'] == user_id:
                # Add the id to the user
                self.users[user['id']]['sticky_roles'].append(role_id) # great coding
                found_user = self.users[user['id']]  # Save the user we found
                break
        
        # Update the database
        with sqlite(DATABASE_NAME) as cur:
            # Use json.dumps to get a string equivalent of the json
            cur.execute('UPDATE guilds SET users=? WHERE guild_id=?', (json.dumps(self.users), self.guild_id))

        return found_user


def get_guild(guild_id):
    """
    Get a guild by its id. Returns the guild if found, None otherwise
    """
    with sqlite(DATABASE_NAME) as cur:
        cur.execute('SELECT * FROM guilds WHERE guild_id=?', (guild_id,))
        return DatabaseGuild(*cur.fetchone())

def init_guild(guild_id, allowed_channels='' | list[int], custom_prefix='!'):
    """
    Initialise a guild in the database, with factory default settings. Returns the new guild object.
    Takes optional allowed channels as a list of ids
    Default settings are:
    - No sticky role ids
    - No users saved
    - Custom prefix ! (can be passed optionally)
    - No allowed channels (can be passed optionally)
    """
    with sqlite(DATABASE_NAME) as cur:
        cur.execute('INSERT INTO guilds VALUES(?, ?, ?, ?, ?)', (guild_id, '', json.dumps([]), custom_prefix, ';'.join(allowed_channels)))