## Guild table (information about guilds)
guild_id >> INTEGER >> id of the guild
sticky_role_ids >> STRING >> List of sticky roles id;id;id
users >> STRING >> JSON of Users in the guild {
    "1": {
        "sticky_roles":[1,2,3],
        "level":7,"xp_to_next":413
        },
    "user_id": {
        "sticky_roles":list,
        "level":int,"xp_to_next":int
    }
}
custom_prefix >> STRING >> Custom prefix for the server i.e. !
allowed_channel_ids >> STRING >> List of channels the bot can respond in id;id;id
