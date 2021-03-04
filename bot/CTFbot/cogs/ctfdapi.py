from requests import Session
from requests.compat import urljoin
import os
from discord.ext import commands, tasks
from time import time,sleep
from datetime import datetime
from discord.utils import get
from CTFbot.tools import get_env

import logging

logger = logging.get_logger(__name__)

CTFD_TOKEN = get_env("CTFD_TOKEN")
CTFD_SITE = get_env("CTFD_SITE")
CTFD_API = get_env("CTFD_API")
CTFD_SUCCESS_UPDATE = float(get_env("CTFD_SUCCESS_UPDATE"))

GUILD_ID = int(get_env("GUILD_ID"))

class CTFDlink:
    def __init__(self):
        self.session = generate_session()
    
    def get_users(self):
        logger.debug("get_users begins")
        req = self.session.get("users",json=True)
        if req.status_code != 200:
            logger.warning(f"Error get_users :  {req.url} {req.status_code}")
            return []
        users = [format_user(u) for u in req.json()["data"]]
        return [u for u in users if u is not None]

    def get_successes(self,user_id):
        logger.debug("get_successes begins.")
        req = self.session.get(f"users/{user_id}/solves",json=True)
        if req.status_code != 200:
            logger.warning(f"Error get_successes {req.url} {req.status_code}")
            return []
        challenges = [{"name":c['challenge']['name'],"date":c['date']} for c in req.json()["data"]]
        return challenges
    

class CTFDnotif(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.link = CTFDlink()
        self._last_update = 0
        self.users = []
        self.update.start()

    @tasks.loop(seconds=CTFD_SUCCESS_UPDATE)
    async def update(self,force=False):
        logger.debug(f"Updating users, last time : {self._last_update")
        self.users = self.link.get_users()
        await self.update_success(force)
        self._last_update = time()

    @update.before_loop
    async def before_update(self):
        logger.debug('waiting bot to be ready...')
        await self.bot.wait_until_ready()

    @commands.command(name="forceroleupdate")
    @commands.has_permissions(administrator=True)
    async def force_update(self,ctx):
        logger.debug(f"forceroleupdate executed by {ctx.author}")
        await self.update(True)

    
    async def update_success(self,force=False):
        logger.debug(f"Update success mode force={force}")
        for user in self.users:
            successes = self.link.get_successes(user['id'])
            for challenge in successes:
                if datetime.fromisoformat(challenge['date']).replace(tzinfo=None)>datetime.fromtimestamp(self._last_update) or force:
                    salon, chan, role = challenge_to_SCR(challenge['name'])
                    if salon is None:
                        continue
                    logger.info(f"Update {user['discord_nick']} for challenge {challenge['name']}, giving {role} ({salon}, {chan})")
                    await self.give_role(role,user['discord_nick'])
        

    async def give_role(self,role_name,discord_nick):
        member = self.bot.get_guild(GUILD_ID).get_member_named(discord_nick)
        logger.debug(f"Giving {role_name} to {discord_nick}")
        if member is None:
            logger.warning(f"Error ctfdapi : user not found : {discord_name} {discr} in {GUILD_ID}")
            return 
        role = get(self.bot.get_guild(GUILD_ID).roles,name=role_name)
        if role is None:
            logger.warning(f"Error Role not found : {role_name} in {GUILD_ID}")
        if role not in member.roles:
            await member.add_roles(role)
        

class APISession(Session):
    """@ctfcli """
    def __init__(self, prefix_url=None, *args, **kwargs):
        super(APISession, self).__init__(*args, **kwargs)
        # Strip out ending slashes and append a singular one so we generate
        # clean base URLs for both main deployments and subdir deployments
        self.prefix_url = prefix_url.rstrip("/") + "/"

    def request(self, method, url, *args, **kwargs):
        # Strip out the preceding / so that urljoin creates the right url
        # considering the appended / on the prefix_url
        url_tmp = urljoin(self.prefix_url, CTFD_API.lstrip("/").rstrip("/")+"/")
        url_tmp = urljoin(url_tmp,url.lstrip("/"))
        return super(APISession, self).request(method, url_tmp, *args, **kwargs)








def format_user(u):
    lst = [t['value'] for t in u['fields'] if t['name']=='Discord ID']
    if len(lst)==0:
        logger.warning(f"Error format_user {u['name']}: no discord id found")
        return None
    discord_id = lst[0]
    return {"id":u['id'],"name":u['name'],"discord_nick":discord_id}

def challenge_to_SCR(chal_name):
        try:
            salon,chan = chal_name.split("-")
        except:
            logger.debug(f"Bad challenge name : {chal_name}")
            return None,None,None
        salon = salon.strip().replace(" ","-").upper()
        chan = chan.strip().replace(" ","-").replace("#","-").lower()
        role = salon.lower()+"-"+chan
        return salon,chan,role

def generate_session():
    s = APISession(prefix_url=CTFD_SITE)
    s.headers.update({"Authorization": f"Token {CTFD_TOKEN}"})
    return s


def setup(bot):
    bot.add_cog(CTFDnotif(bot))
