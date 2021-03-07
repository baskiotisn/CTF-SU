from importlib import import_module
from discord.ext import commands

import logging

logger = logging.getLogger(__name__)

### Todo : remplacer l'import module par une gestion bdd/plus flexbile.

class CTFChecker(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.command(name="CTF")
    @commands.dm_only()
    async def check_flag(self,ctx,name,*,reponse):
        """  Valider un challenge : CTF nom_challenge réponse """
        
        logger.debug(f"check_flag {ctx.author} {name} {reponse}")
        txt = treat_CTF(name,reponse)
        logger.debug(f"Response sent : {txt}")
        await ctx.send(txt)
    
def treat_CTF(name,reponse):
    try:
        chal_module = import_module("."+name,"CTFbot")
    except Exception as e:
        logger.warning(f"Error in treat_CTF {name} : {e}")
        return f"Challenge {name} inexistant"
    try:
        return chal_module.checkflag(reponse)
    except Exception as e:
        logger.warning(f"Error in checkflag {name} {reponse} : {e}")
        return "Probleme lors du calcul de la réponse."

def setup(bot):
    bot.add_cog(CTFChecker(bot))
