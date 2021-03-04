import os
import discord  
from discord.ext import commands

from os import listdir
from os.path import isfile, join
import traceback
import logging
from logging.handlers import RotatingFileHandler
logging.basicConfig(level=eval("logging."+os.getenv("LOG_LEVEL", "INFO")))
logger = logging.getLogger(__name__)

if os.getenv("LOG_FILE"):
    handler = RotatingFileHandler(os.getenv("LOG_FILE"),maxBytes=2000000,backupCount=10)
    handler.setLevel(logger.level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger('').addHandler(handler)


cogs_dir = os.getenv("COGS_DIR","cogs")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!",intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as : {bot.user.name} - {bot.user.id}')

abs_dir_cog = join(os.path.dirname(__file__),cogs_dir)
for extension in [f.replace('.py','') for f in listdir(abs_dir_cog) if isfile(join(abs_dir_cog,f))]:
    try:
        logger.info(f"Loading {cogs_dir}.{extension}...")
        bot.load_extension("."+cogs_dir+"."+extension,package="CTFbot")
    except (discord.ClientException,discord.DiscordException, ModuleNotFoundError) as e:
        logger.info(f'Failed to load extension {extension} {e}')
        traceback.print_exc()
