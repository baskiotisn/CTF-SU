from importlib import import_module
from discord.ext import commands
import subprocess
import logging
import time

logger = logging.getLogger(__name__)


class InterfaceShell(commands.Cog):

    LST_SHELL   = dict()

    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="shell")
    async def shell(self, ctx, cmd, *, args):
        """  Lance un shell interactif pour le challenge name """

        logger.debug(f"interface shell {ctx.author} {cmd} {args}")
        if ctx.author.dm_channel is None or ctx.message.channel.id != ctx.author.dm_channel.id:
            await ctx.message.delete()
            channel = await ctx.message.author.create_dm()
            await channel.send(f"{ctx.author.mention} création de shell uniqument en DM !!!")
            logger.debug(f"Not DM")
            return
        txt = self.parse_cmd(ctx.author.id,cmd, args)
        logger.debug(f"Response sent : {txt}")
        await ctx.send(txt)

    def parse_cmd(self,author_id,cmd,*,args):
        if cmd == "init":
            return self.init_shell(author_id,args)
        if cmd == "close":
            return self.close_shell(author_id)
        if author_id not in self.LST_SHELL:
            return f"Pas de shell ouvert, ouvres en un d'abord (**{self.bot.command_prefix}shell init**)" 
        return self.LST_SHELL[author_id].cmd(cmd,args)

    def init_shell(self,author_id,name):
        if author_id in self.LST_SHELL:
            return f"Déjà un shell ouvert, ferme le d'abord : **{self.bot.command_prefix}shell close**)"
        try:
            chal_module = import_module("."+name, "CTFbot")
        except Exception as e:
            logger.warning(f"Error in InterfaceShell init_shell {name} : {e}")
            return f"Challenge {name} inexistant"
        shell = LocalShell(chal_module.get_exec(),chal_module.get_timeout())
        self.LST_SHELL[author_id] = shell
        return f"shell pour {name} initié"

    def close_shell(self,author_id):
        if author_id not in self.LST_SHELL:
            return f"Pas de shell ouvert"
        self.LST_SHELL[author_id][0].close()
        del self.LST_SHELL[author_id]




    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            command = ctx.message.content.split()[0]
            await ctx.send("Il manque des arguments à la commande "+command)


class LocalShell:

    def __init__(self, exec,timeout):
        self.proc = subprocess.Popen(
            exec, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stder=subprocess.PIPE)
        self.timeout = time()+timeout

    def cmd(self, args):
        self.proc.stdin.write(args)
        self.proc.stdin.flush()
        return self.proc.stdout.readlines().decode('utf-8').strip()

    def close(self):
        self.proc.stdin.close()
        self.proc.terminate()
        self.proc.wait(timeout=0.2)
