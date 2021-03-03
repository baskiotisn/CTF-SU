from requests import Session
from requests.compat import urljoin
import os
import json
from discord.ext import commands
from time import time
import discord
CTFD_TOKEN = os.getenv("CTFD_TOKEN")
CTFD_SITE = os.getenv("CTFD_SITE")
CTFD_API = os.getenv("CTFD_API")
CTFD_SUCCESS_UPDATE = float(os.getenv("CTFD_SUCCESS_UPDATE"))
CTFD_USERS_UPDATE = float(os.getenv("CTFD_USERS_UPDATE"))


class CTFDlink:
    def __init__(self):
        self.session = generate_session()
    
    def get_users(self):
        req = s.get("users",json=True)
        if req.status_code != 200:
            print(f"error {req.url} {req.status_code}")
        users = [format_user(u) for u in req.json()["data"]]
        return users

    def get_successes(self,user_id):
        req = s.get(f"users/{user_id}/solves",json=True)
        if req.status_code != 200:
            print(f"error {req.url} {req.status_code}")
        challenges = [{"name":c['challenge']['name'],"date":c['date']} for c in req.json()]
        return challenges
    

class CTFDnotif(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.link = CTFDlink()
        self._last_update = 0
        self.users = []
        print("ici ou la c'est pareil")
    
    async def update(self,force=False):
        now = time()
        if (now-self._last_update)>CTFD_USERS_UPDATE or force:
            self.users = self.link.get_users()
        if (now-self._last_update)>CTFD_SUCCES_UPDATE or force:
            await self.update_success(force)
        self._last_update = now
    
    @commands.command(name="forceroleupdate")
    @commands.has_permissions(administrator=True)
    async def force_update(ctx,self):
        print("lalala")
        await self.update(True)

    
    async def update_success(self,force=False):
        print("ici")
        for user in self.users:
            if user['name'] not in ["baskiotisn"]:
                continue
            successes = self.link.get_successes(user['id'])
            for challenge in successes:
                if challenge['date']>self._last_update or force:
                    salon, chan, role = challenge_to_SCR(challenge['name'])
                    await self.give_role(role,user['discord_nick'])
        

    async def give_role(self,role: discord.Role, member: discord.Member):
        if role not in member.roles:
            await member.add_role(role)

    

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
        return None
    discord_id = lst[0]
    if "#" not in discord_id:
        return None
    return {"id":u['id'],"name":u['name'],"discord_nick":"".join(lst[0].split("#")[:-1]),"discord_id":lst[0].split("#")[-1]}

def challenge_to_SCR(chal_name):
        try:
            salon,chan = chal_name.split("-")
        except:
            print(f"Mauvais nom de challenge : {chal_name}")
            return
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