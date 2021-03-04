import sqlite3
import discord
from discord.ext.commands import has_permissions
from discord.ext import commands
from discord.utils import get
import unicodedata
import os
import logging
from CTFbot.tools import get_env

logger = logging.getLogger(__name__)

DIC_MENUROLE = dict()
TABLE_NAME = "MenuRole_TABLE"
EMOJIS = ["one","two","three","four","five","six","seven","eight","nine"]


DB_SQLITE = get_env('DB_SQLITE')
GUILD_ID = int(get_env("GUILD_ID"))

class MenuRole(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        
    @commands.command(name="menurole")
    @has_permissions(administrator=True)
    async def create_menu_role(self,ctx,chan,titre,*args):
        """ Construit un menu de roles : menurole channel  message role1  role2 ... """
        
        logger.debug(f"create_menu_role {ctx.author} {chan} {titre} {''.join(a for a in args)}")
        chan = discord.utils.get(self.bot.get_guild(GUILD_ID).channels,name=chan)
        if chan is None:
            await ctx.author.send(f"Le channel {chan} n'a pas été trouvé")
            logger.debug(f" -> failed : no {chan} found in guild {GUILD_ID}")
            return

        options = []
        for i in range(len(args)):
            role_name, smiley = args[i],EMOJIS[i]
            role = get(chan.guild.roles,name=role_name)
            if role is None:
                role = await chan.guild.create_role(name=role_name)
                logger.debug(f"{role_name} not existing, create role for guild {chan.guild}")
            options.append((role,smiley,role.id))
        
        
        msg = f"**{titre}**\n\n"
        msg += "\n".join( f"\t:{smiley}: => {role_name}" for role_name,smiley,role_id in options)
        posted_msg = await chan.send(msg)
        logger.debug(f"message sent in {chan}: {msg}")
        DIC_MENUROLE[posted_msg.id] = (posted_msg.id,titre,options)
        _menurole_add_db(posted_msg.id)
        return posted_msg.id


    @commands.Cog.listener()
    async def on_raw_reaction_add(self,payload):
        logger.debug(f"reaction_add {payload.guild_id} {payload.user_id} {payload.message_id} {payload.emoji}.")
        if payload.message_id not in DIC_MENUROLE:
            logger.debug(f"message not tracked.")
            return
        role_id, other_roles_id = _treat_reaction_payload(payload)
        if role_id is None:
            return
        role = self.bot.get_guild(payload.guild_id).get_role(role_id)
        if role is None:
            logger.warning(f"role not existing : reaction_add {payload.guild_id} {payload.user_id} {payload.message_id} {role_id}")
            return
        user = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
        if user is None:
            logger.warning(f"member {payload.user_id} not found")
            return
        await user.add_roles(role)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self,payload):
        logger.debug(f"reaction_remove {payload.guild_id} {payload.user_id} {payload.message_id}.")
        if payload.message_id not in DIC_MENUROLE:
            logger.debug(f"message not tracked.")
            return
        role_id, other_roles_id = _treat_reaction_payload(payload)
        if role_id is None : 
            return
        role = self.bot.get_guild(payload.guild_id).get_role(role_id)
        if role is None:
            logger.warning(f"role not existing : reaction_add {payload.guild_id} {payload.user_id} {payload.message_id} {role_id}")
            return
        user =  self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
        if user is None:
            logger.warning(f"member {payload.user_id} not found")
            return
        await user.remove_roles(role)


def _treat_reaction_payload(payload):
    message_id = payload.message_id
    emoji = payload.emoji
    if emoji.is_custom_emoji():
        logger.debug(f"custom emoji not recognized.")
        return None, None
    reac = unicodedata.name(emoji.name[0]).split(" ")[-1].lower()
    options = DIC_MENUROLE[message_id][2]
    role_id = [id for r, s, id in options if s == reac]
    other_roles_id = [id for r, s, id in options if s != reac]
    if len(role_id) == 0:
        logger.debug(f"emoji not recognized")
        return None, None
    return role_id[0], other_roles_id


def _menurole_add_db(id_msg):
    id_msg, titre, options = DIC_MENUROLE[id_msg]
    options = "|".join(f"{k} {v} {m}" for k,v,m in options)
    conn = sqlite3.connect(DB_SQLITE)
    c = conn.cursor()
    c.execute(f'INSERT into {TABLE_NAME} values ("{id_msg}","{titre}","{options}")')
    c.close()
    conn.commit()
    conn.close()
    logger.debug(f"Tuple {id_msg} {titre} {options} inserted to {TABLE_NAME} ({DB_SQLITE})")

def _menurole_load_from_db():
    conn = sqlite3.connect(DB_SQLITE)
    c = conn.cursor()
    for row in c.execute(f'SELECT id_msg,titre,options from {TABLE_NAME}'):
        options = []
        for s in row[2].split("|"):
            options.append(s.split(" "))
        
        DIC_MENUROLE[row[0]] = (row[0],row[1],[(o[0],o[1],int(o[2])) for o in options])
        logger.debug(f"MenuRole loaded : {row[0]} {row[1]} {row[2]}")
    c.close()
    conn.close()

def setup(bot):
    conn = sqlite3.connect(DB_SQLITE)
    c = conn.cursor()
    c.execute(
        f'CREATE TABLE IF NOT EXISTS {TABLE_NAME} (id_msg integer, titre text, options text)')
    c.close()
    conn.close()
    _menurole_load_from_db()
    bot.add_cog(MenuRole(bot))
    
