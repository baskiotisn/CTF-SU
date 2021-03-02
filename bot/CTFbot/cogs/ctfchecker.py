from importlib import import_module
from discord.ext import commands

### Todo : remplacer l'import module par une gestion bdd.
class CTFChecker(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.command(name="CTF",help="Valider un challenge. Usage : !CTF nom_challenge réponse")
    async def check_flag(self,ctx,name,*,reponse):
        
        if ctx.author.dm_channel is None or ctx.message.channel.id != ctx.author.dm_channel.id:
            await ctx.message.delete()
            channel = await ctx.message.author.create_dm()
            await channel.send(f"{ctx.author.mention} communique ta réponse en DM !!!")
            return
        txt = treat_CTF(name,reponse)
        await ctx.send(txt)

    @commands.Cog.listener()
    async def on_command_error(self,ctx,error):
        if isinstance(error,commands.MissingRequiredArgument):
            command = ctx.message.content.split()[0]
            await ctx.send("Il manque des arguments à la commande "+command)

def treat_CTF(name,reponse):
    try:
        chal_module = import_module("."+name,"CTFbot")
    except Exception as e:
        print(e)
        return f"Challenge {name} inexistant"
    try:
        return chal_module.checkflag(reponse)
    except Exception as e:
        return str(e)

def setup(bot):
    bot.add_cog(CTFChecker(bot))
