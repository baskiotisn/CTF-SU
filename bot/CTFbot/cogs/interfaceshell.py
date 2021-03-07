from importlib import import_module
from discord.ext import commands,tasks
import subprocess
import logging
import time
import threading
import subprocess
from queue import Queue
from time import time, sleep
import asyncio


logger = logging.getLogger(__name__)


class InterfaceShell(commands.Cog):

    LST_SHELL   = dict()
    
    def __init__(self,bot):
        self.bot = bot
        self.check_alive.start()
    
    @commands.group(name="shell",invoke_without_command=True)
    @commands.dm_only()
    async def shell(self, ctx,*args):
        """  Shell interactif pour certains challenges. Une fois le shell ouvert, transmettre les commandes avec 
        """
        pref = self.bot.command_prefix
        help = f"Utilise :\n * `{pref}shell init nom_challenge` pour initialiser le shell\n * `{pref}shell cmd ta_commande` pour envoyer une commande au shell\n * `{pref}shell close` pour fermer le shell"
        if len(args)==0:
            await ctx.send(help)
            return
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Commande non trouvée.\n"+help)
        return
        
    @shell.command(name="cmd")
    @commands.dm_only()
    async def cmd(self,ctx,*,args):
        """ Execute une commande sur le shell """
        
        if ctx.author.id not in self.LST_SHELL:
            await ctx.send(f"Pas de shell ouvert, ouvres en un d'abord (**{self.bot.command_prefix}shell init nom_du_challenge**)")
            return
        if not self.LST_SHELL[ctx.author.id].isalive():
            self.LST_SHELL[ctx.author.id].close()
            del self.LST_SHELL[ctx.author.id]
            await ctx.send(f"Précédent shell fermé, ouvres un nouveau shell")
            return
        await ctx.send("`"+self.LST_SHELL[ctx.author.id].cmd(args)+"`")

        
    @shell.command(name="init")
    @commands.dm_only()
    async def init_shell(self, ctx, name):
        """ Permet d'initialiser un shell : **shell init nom_du_challenge ** """
        logger.debug(f"shell init {name} par {ctx.author}")
        if ctx.author.id in self.LST_SHELL:
            if self.LST_SHELL[ctx.author.id].isalive():
                await ctx.send(f"Déjà un shell ouvert, ferme le d'abord : **{self.bot.command_prefix}shell close**)")
                return
            else:
                self.LST_SHELL[ctx.author.id].close()
                del self.LST_SHELL[ctx.author.id]
        try:
            chal_module = import_module("."+name, "CTFbot")
        except Exception as e:
            logger.warning(f"Error in InterfaceShell init_shell {name} : {e}")
            await ctx.send(f"Challenge {name} inexistant")
            return
        shell = LocalShell(chal_module.get_exec(),chal_module.get_timeout())
        self.LST_SHELL[ctx.author.id] = shell
        await ctx.send(f"shell pour {name} initialisé, timeoute de {chal_module.get_timeout()}s")
        msg = shell.run()
        await ctx.send("`"+msg+"`")
    
    @shell.command(name="close")
    @commands.dm_only()
    async def close_shell(self,ctx):
        """ Ferme une session shell """
        logger.debug(f"shell close par {ctx.author}")
        if ctx.author.id not in self.LST_SHELL:
            await ctx.send(f"Pas de shell ouvert")
            return
        self.LST_SHELL[ctx.author.id].close()
        del self.LST_SHELL[ctx.author.id]
        await ctx.send(f"shell fermé")

    @tasks.loop(seconds=10)
    async def check_alive(self):
        lst = list(self.LST_SHELL.items())
        for id, shell in lst:
            if not shell.isalive() or shell.timeout<time():
                shell.close()
                del self.LST_SHELL[id]

    @check_alive.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
   



class LocalShell:

    def __init__(self,exec,timeout=3600):
        self.proc = subprocess.Popen(exec,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0)
        self.start_date = time()
        self.queue = Queue()
        self.thread = None
        self.timeout = time()+timeout

    def isalive(self):
        return self.thread is not None and self.proc.returncode is None and self.thread.is_alive()

    def run(self):
        self.thread = threading.Thread(target=self.read_atom, args=())
        self.thread.start()
        sleep(0.01)
        return self.read_block()
        
    def cmd(self,cmd):
        if not self.isalive():
            return "Shell fermé, reouvres-en un."
        try:
            self.proc.stdin.write(cmd.encode()+b'\n')
            self.proc.stdin.flush()
            sleep(0.01)
        except BrokenPipeError as e :
            self.thread = None
            return "Shell fermé, reouvres-en un"
        return self.read_block()
    def close(self):
        self.proc.stdin.close()
        self.proc.stdout.close()
        self.thread = None
        self.proc.terminate()
        self.proc.wait(timeout=0.2)

    def read_block(self):
        msg = ""
        while not self.queue.empty():
            msg+=self.queue.get().decode()
        return msg

    def read_atom(self):
        try:
            while self.isalive():
                d = self.proc.stdout.read(1)
                if not d or self.proc.returncode is not None or self.thread is None:
                    break
                self.queue.put(d)
        except EOFError:
            pass

def setup(bot):
    bot.add_cog(InterfaceShell(bot))

