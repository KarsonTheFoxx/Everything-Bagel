import json
import sqlite3

from database_utils import sqlite, xp_for_next_level

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
    def __init__(self, guild_id, sticky_role_ids, users, custom_prefix, allowed_channel_ids):
        self.guild_id = guild_id
        self.sticky_role_ids = list(map(int, filter(None, sticky_role_ids.split(';')))) if sticky_role_ids != '' else []
        self.users = json.loads(users)
        self.custom_prefix = custom_prefix
        self.allowed_channel_ids = map(int, allowed_channel_ids.split(';'))
    
    def init_user(self, user_id: int) -> bool:
        """
        Initialise a user into the users column if they have not been initialised yet. Returns True if they were initialised, 
            False otherwise (they already existed in the db.)
        Commonly run in add_sticky_role_to_user function to make user that a user can be accesssed.
        """
        # check if the user already exists
        if self.users.get(str(user_id)): return False
        
        # Initliase the user
        self.users[str(user_id)] = {'sticky_roles':[],'level':1,'xp_to_next':xp_for_next_level(1)}

        # Update the database
        with sqlite(DATABASE_NAME) as cur:
            # Use json.dumps to get a string of the json data which the database can use
            cur.execute('UPDATE guilds SET users=? WHERE guild_id=?', (json.dumps(self.users), self.guild_id))
        
        return True # The user was initialised

    def create_sticky_role(self, role_id: int) -> list:
        """
        Add a role id to the list of stick role ids. Returns an empty list if the role is already added, and the current 
        """
        if role_id in self.sticky_role_ids:
            return []
        with sqlite(DATABASE_NAME) as cur:
            # Do not add a comma if this is the first id you are adding
            cur.execute('UPDATE guilds SET sticky_role_ids=sticky_role_ids || ";" || ? WHERE guild_id=?', (int(role_id), self.guild_id))
            # Update the bot data
            self.sticky_role_ids.append(role_id)
            return self.sticky_role_ids
    
    def remove_sticky_role(self, role_id: int) -> list:
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
    
    def channel_valid(self, channel_id: int) -> bool:
        """
        Returns if the given channel id is one that the bot is configured to respond in
        """
        return channel_id in self.allowed_channel_ids

    def add_sticky_role_to_user(self, user_id: int, role_id: int) -> dict:
        """
        Add a sticky role to a user. Returns their new json if successful, an empty dict if the role isn't sticky.
        **THIS COMMANDS ASSUMES THE USER ID IS VALID AND WILL ALWAYS ADD IT TO THE DATABASE**
        """
        self.init_user(user_id) # Make sure the user is initialised in the database.
        if role_id not in self.sticky_role_ids or role_id in (self.users.get(str(user_id)) or {}).get('sticky_roles'):
            return {}
        
        # Add the sticky role using the JSON
        self.users[str(user_id)]['sticky_roles'].append(role_id) # great coding
        
        # Update the database
        with sqlite(DATABASE_NAME) as cur:
            # Use json.dumps to get a string equivalent of the json
            cur.execute('UPDATE guilds SET users=? WHERE guild_id=?', (json.dumps(self.users), self.guild_id))

        return self.users[str(user_id)]

    def give_user_xp(self, user_id: int, xp: int) -> int:
        """
        Add xp to a user's local level in the guild. Returns their new level if they levelled up, 0 otherwise.
        """
        if xp > 1_000_000:
            raise ValueError('XP value may not be above 1,000,000')
        # Find the user
        user_xp = self.users[str(user_id)]['xp_to_next']
        user_level = self.users[str(user_id)]['level']
        self.users[str(user_id)]['xp_to_next'] -= xp

        # Check if the user has levelled up
        new_xp = self.users[str(user_id)]['xp_to_next']
        if new_xp <= 0:
            self.users[str(user_id)]['level'] += 1
            # +new_xp so that any overflow (negative) will count into the new level
            new_xp_requirement = xp_for_next_level(user_level+1)
            self.users[str(user_id)]['xp_to_next'] = xp_for_next_level(user_level+1)+new_xp

            # If the amount of xp that overflows is more than the xp of the new level that we can "spend"
            # (we need to level up more than one level)
            if new_xp_requirement <= abs(new_xp):
                # Rerun the command recursively until it reaches a point where it has "spent" the overflow xp on new levels
                self.give_user_xp(user_id, 0)

        # Update the database
        with sqlite(DATABASE_NAME) as cur:
            cur.execute('UPDATE guilds SET users=? WHERE guild_id=?', (json.dumps(self.users), self.guild_id))
        
        # Return the new level if they levelled up
        if user_xp-xp <= 0: return user_level+1
        else: return 0

def get_guild(guild_id: int)-> DatabaseGuild | None:
    """
    Get a guild by its id. Returns the guild if found, None otherwise
    """
    with sqlite(DATABASE_NAME) as cur:
        cur.execute('SELECT * FROM guilds WHERE guild_id=?', (guild_id,))
        data = cur.fetchone()
        return DatabaseGuild(*data) if data else None

def init_guild(guild_id, allowed_channels='', custom_prefix='!'):
    """
    Initialise a guild in the database, with factory default settings. Returns the new guild object, or the guild object if it already exists.
    Takes optional allowed channels as a list of ids
    Default settings are:
    - No sticky role ids
    - No users saved
    - Custom prefix ! (can be passed optionally)
    - No allowed channels (can be passed optionally)
    """
    with sqlite(DATABASE_NAME) as cur:
        default_values = (guild_id, '', json.dumps({}), custom_prefix, ';'.join(allowed_channels))
        try:
            cur.execute('INSERT INTO guilds VALUES(?, ?, ?, ?, ?)', default_values)
        except sqlite3.IntegrityError:
            return get_guild(guild_id)
        else:
            return DatabaseGuild(*default_values)
