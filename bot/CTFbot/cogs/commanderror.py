import discord
import traceback
import sys
from discord.ext import commands
import logging
logger = logging.getLogger()

class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
         return


        if hasattr(ctx.command, 'on_command_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return


        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f'Command pas trouvé')
            return
        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')
            return

        if isinstance(error,commands.errors.PrivateMessageOnly):
            await ctx.message.delete()
            channel = await ctx.message.author.create_dm()
            await channel.send(f'{ctx.command} ne peut être exécuté que en message privé !!')
            return
        # For this error example we check to see where it came from...
        if isinstance(error, commands.BadArgument):
            await ctx.send('Mauvais arguments passés')
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Il manque des arguments à la commande')
            return
        # All other Errors not returned come here. And we can just print the default TraceBack.
        logger.error(f'Ignoring exception in command {ctx.command} : {type(error)} {error} {error.__traceback__}')

    """
    @commands.command(name='repeat', aliases=['mimic', 'copy'])
    async def do_repeat(self, ctx, *, inp: str):
        await ctx.send(inp)

    @do_repeat.error
    async def do_repeat_handler(self, ctx, error):
       
        # Check if our required argument inp is missing.
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'inp':
                await ctx.send("You forgot to give me input to repeat!")
    """

def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
