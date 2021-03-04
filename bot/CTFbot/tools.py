import discord
import os


def get_env(name):
    var = os.getenv(name)
    if var is None:
        raise discord.DiscordException(f"env file must declare {name} !!")
    return var
        