import os
from dotenv import load_dotenv
import discord  
from discord.ext import commands

from os import listdir
from os.path import isfile, join
import traceback

DB_SQLITE = os.getenv('DB_SQLITE')
cogs_dir = os.getenv("COGS_DIR")
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!",intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as : {bot.user.name} - {bot.user.id}')

abs_dir_cog = join(os.path.dirname(__file__),cogs_dir)
for extension in [f.replace('.py','') for f in listdir(abs_dir_cog) if isfile(join(abs_dir_cog,f))]:
    try:
        print(f"Loading {cogs_dir}.{extension}...")
        bot.load_extension("."+cogs_dir+"."+extension,package="CTFbot")
    except (discord.ClientException, ModuleNotFoundError) as e:
        print(f'Failed to load extension {extension} {e}')
        traceback.print_exc()
