from dotenv import load_dotenv
import os
from pathlib import Path
import sys

if "__main__"==__name__:
    if "-d" in sys.argv and os.path.exists(Path(".")/".debug.env"):
        
        load_dotenv(dotenv_path=Path('.')/'.debug.env')
    else:
        load_dotenv()



    from CTFbot import bot
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.command_prefix = os.getenv('CMD_PREFIX')
    bot.run(TOKEN)
