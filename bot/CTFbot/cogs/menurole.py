import sqlite3
import discord
from discord.ext.commands import has_permissions
from discord.ext import commands
from discord.utils import get
import unicodedata
import os

DIC_MENUROLE = dict()
TABLE_NAME = "MenuRole_TABLE"
EMOJIS = ["one","two","three","four","five","six","seven","eight","nine"]

DB_SQLITE = os.getenv('DB_SQLITE')

class MenuRole(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="role")
    @has_permissions(administrator=True)
    async def create_menu_role(self,ctx,chan,titre,*args):
        """ /role chan  'Choisir un role...'  role1 role2 " """
        
        chan = discord.utils.get(self.bot.get_all_channels(),name=chan)
        if chan is None:
            return None
        options = []
        for i in range(len(args)):
            role_name, smiley = args[i],EMOJIS[i]
            role = get(ctx.guild.roles,name=role_name)
            if role is None:
                role = await ctx.guild.create_role(name=role_name)
            options.append((role,smiley,role.id))

        msg = f"**{titre}**\n\n"
        msg += "\n".join( f"\t:{smiley}: => {role_name}" for role_name,smiley,role_id in options)
        posted_msg = await chan.send(msg)
        DIC_MENUROLE[posted_msg.id] = (posted_msg.id,titre,options)
        _menurole_add_db(posted_msg.id)
        return posted_msg.id


    @commands.Cog.listener()
    async def on_raw_reaction_add(self,payload):
        role_id, other_roles_id = _treat_reaction_payload(payload)
        if role_id is None: return
        role = self.bot.get_guild(payload.guild_id).get_role(role_id)
        user = await self.bot.get_guild(payload.guild_id).fetch_member(payload.user_id)
        await user.add_roles(role)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self,payload):
        if payload.message_id not in DIC_MENUROLE: return
        role_id, other_roles_id = _treat_reaction_payload(payload)
        if role_id is None : return
        role = self.bot.get_guild(payload.guild_id).get_role(role_id)
        user = await self.bot.get_guild(payload.guild_id).fetch_member(payload.user_id)
        await user.remove_roles(role)


def _treat_reaction_payload(payload):
    message_id = payload.message_id
    emoji = payload.emoji
    if emoji.is_custom_emoji():
        return None, None
    if message_id not in DIC_MENUROLE:
        return None, None
    reac = unicodedata.name(emoji.name[0]).split(" ")[-1].lower()
    options = DIC_MENUROLE[message_id][2]
    role_id = [id for r, s, id in options if s == reac]
    other_roles_id = [id for r, s, id in options if s != reac]
    if len(role_id) == 0:
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

def _menurole_load_from_db():
    
    conn = sqlite3.connect(DB_SQLITE)
    c = conn.cursor()
    for row in c.execute(f'SELECT id_msg,titre,options from {TABLE_NAME}'):
        options = []
        for s in row[2].split("|"):
            options.append(s.split(" "))
        
        DIC_MENUROLE[row[0]] = (row[0],row[1],[(o[0],o[1],int(o[2])) for o in options])
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
    
