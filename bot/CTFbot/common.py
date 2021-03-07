import os
import discord  
from discord.ext import commands

from os import listdir
from os.path import isfile, join
import traceback
import logging
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter

class DiscordFilter(logging.Filter):
    def filter(self,record):
        return not record.name.startswith("discord")

EXCLUDE_COGS = eval(os.getenv("EXCLUDE_COGS","[]"))

LOGFORMAT = " %(log_color)s%(levelname)-8s:%(name)s%(reset)s | %(log_color)s%(message)s%(reset)s"
LOG_LEVEL = eval("logging."+os.getenv("LOG_LEVEL","INFO"))
LOG_FILE_LEVEL = eval("logging."+os.getenv("LOG_FILE_LEVEL","DEBUG"))
handler = logging.StreamHandler()
handler.setLevel(LOG_LEVEL)
handler.setFormatter(ColoredFormatter(LOGFORMAT))
handler.addFilter(DiscordFilter())
handlers = [handler]

if os.getenv("LOG_FILE"):
    handler = RotatingFileHandler(os.getenv("LOG_FILE"),maxBytes=2000000,backupCount=10)
    handler.setLevel(LOG_FILE_LEVEL)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.addFilter(DiscordFilter())
    handlers.append(handler)
logging.basicConfig(level=logging.DEBUG,handlers=handlers)
logger = logging.getLogger(__name__)

cogs_dir = os.getenv("COGS_DIR","cogs")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!",intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as : {bot.user.name} - {bot.user.id}')

abs_dir_cog = join(os.path.dirname(__file__),cogs_dir)
for extension in [f.replace('.py','') for f in listdir(abs_dir_cog) if isfile(join(abs_dir_cog,f))]:
    if extension in EXCLUDE_COGS:
        continue
    try:
        logger.info(f"Loading {cogs_dir}.{extension}...")
        bot.load_extension("."+cogs_dir+"."+extension,package="CTFbot")
    except (discord.ClientException,discord.DiscordException, ModuleNotFoundError) as e:
        logger.info(f'Failed to load extension {extension} {e}')
        traceback.print_exc()
