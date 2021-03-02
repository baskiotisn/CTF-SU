from CTFbot import bot
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
