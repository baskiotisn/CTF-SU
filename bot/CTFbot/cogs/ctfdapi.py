from discord.ext.commands.core import dm_only
from requests import Session
from requests.compat import urljoin
import os
from discord.ext import commands, tasks
from time import time,sleep
from datetime import datetime
from discord.utils import get
from CTFbot.tools import get_env
import json
import logging
import discord

logger = logging.getLogger(__name__)

CTFD_TOKEN = get_env("CTFD_TOKEN")
CTFD_SITE = get_env("CTFD_SITE")
CTFD_API = get_env("CTFD_API")
CTFD_SUCCESS_UPDATE = float(get_env("CTFD_SUCCESS_UPDATE"))

GUILD_ID = int(get_env("GUILD_ID"))

class CTFDlink:
    def __init__(self):
        self.session = generate_session()
    
    def get_users(self):
        """ return the list of the ctfd users:
            :return: [{"id":ctfd_id,"name":ctfd_name,"discord_nick":discord_nick}]
        """
        req = self.session.get("users",json=True)
        data = _treat_req(req)
        if data is None: return []
        users = [_format_user(u) for u in data]
        return [u for u in users if u is not None]

    def get_teams(self):
        """ return the list of the ctfd challenges :
            :return: [{"name":team_name, membres":[{"discord_nick","id"}],"challenges":[{"name":name,"date":date}]}]
        """
        users = { u['id']:u for u in self.get_users()}
        req = self.session.get("teams",json=True)
        data = _treat_req(req)
        if data is None: return []
        teams = []
        for team in data:
            members = [ {"discord_nick":users[id]['discord_nick'], "id":id}  for id in self.session.get(f"teams/{team['id']}").json()["data"]["members"] if id in users]
            solves = [{"name":c["challenge"]["name"],"date":c["date"]} for c in  self.session.get(f"teams/{team['id']}/solves").json()["data"]]
            teams.append({"name":team["name"],"captain_id":team["captain_id"], "id":team["id"],"membres":members,"challenges":solves})
        return teams
        
    def get_user_successes(self,user_id):
        """ return the list of challenges success for user_id :
            :return: [{"name":chal_name, "date":date}] 
        """
        req = self.session.get(f"users/{user_id}/solves",json=True)
        data = _treat_req(req)
        if data is None: return []
        challenges = [{"name": c['challenge']['name'], "date":c['date']}
                      for c in data]
        return challenges

    def get_challenges(self):
        """ return the list of challenges 
            :return: [{"name":"chal_name","id":"chal_id"}]
        """
        req = self.session.get(f"challenges",json=True)
        data =_treat_req(req)
        if data is None: return []
        challenges = [{"name":c["name"],"id":c["id"]} for c in data]
        return challenges

    def get_challenge(self,id):
        """ return the detail of the challenge id
            :return: {}
        """

        req = self.session.get(f"challenges/{id}",json=True)
        data = _treat_req(req)
        if data is None: return None
        chal_details = {"name":data["name"],"description":data["description"],"id":data["id"],"value":data["value"]}
        return chal_details

    def reset_pwd(self,user, pwd):
        """ reset le password de l'utilisateur """
        req = self.session.get(f"users/{user['id']}",json=True)
        data = _treat_req(req)
        if data is None: return False
        data["password"] = pwd
        req = self.session.patch(f"users/{user['id']}",json=data)
        data =_treat_req(req)
        if data is None: return False
        return True

    def reset_team_pwd(self,team,pwd):
        req = self.session.get(f"teams/{team['id']}",json=True)
        data = _treat_req(req)
        if data is None: return False
        data["password"] = pwd
        req = self.session.patch(f"teams/{team['id']}",json=data)
        data =_treat_req(req)
        if data is None: return False
        return True



class CTFDnotif(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.link = CTFDlink()
        self._last_update = 0
        self.users = []
        self.update.start()

    @tasks.loop(seconds=CTFD_SUCCESS_UPDATE)
    async def update(self,force=False):
        """ 
            Main loop for the update, call update_successes
        """

        logger.debug(f"Loop update start, last time : {datetime.fromtimestamp(self._last_update)}")
        now = time()
        await self.update_chan_challenges(force)
        await self.update_successes(force)
        self._last_update = now
        logger.debug(f"Loop update end  at {datetime.fromtimestamp(self._last_update)}")
        

    @update.before_loop
    async def before_update(self):
        logger.debug('CTFDnotif waiting bot to be ready...')
        await self.bot.wait_until_ready()

    @commands.command(name="ctfdupdate")
    @commands.has_permissions(administrator=True)
    async def ctfd_update(self,ctx):
        """ MAJ forcée de CTFD pour les créations de chan et l'attribution des roles  """
        logger.debug(f"ctfd_update executed by {ctx.author}")
        await self.update(True)


    async def update_chan_challenges(self,force=False):
        guild = self.bot.get_guild(GUILD_ID)
        challenges = self.link.get_challenges()
        for chal in challenges:
            salon_name, chan_name, role_name = challenge_to_SCR(chal["name"])
            if salon_name is None:
                logger.warning(f"Can not parse {chal['name']} !!")
                continue
            role = get(guild.roles,name=role_name)
            if role is None or force:
                chal_details = self.link.get_challenge(chal['id'])
                if chal_details is None:
                    logger.warning(f"challenge not found!! {chal['id']}")
                    continue
                await self.create_chan(chal_details)


    async def update_successes(self,force=False):
        """ Update roles for teams when challenges are successfull
            :param: force : force the update if True otherwise only if challenge has been solved after the last update
        """
        teams = self.link.get_teams()
        for team in teams:
            for challenge in team["challenges"]:
                if _date_after(challenge['date'],self._last_update) or force:
                    salon_name, chan_name, role_name = challenge_to_SCR(challenge['name'])
                    if salon_name is None:
                        logger.warning(f"Category {salon_name} not found (for challenge {challenge['name']}) !!")
                        continue
                    await self.send_notif_success(challenge,team,salon_name)
                    for user in team["membres"]:
                        logger.debug(f"Update {user['discord_nick']} for challenge {challenge['name']}, examining {role_name} ({salon_name}, {chan_name})")
                        await self.give_role(role_name,user["discord_nick"])

    async def send_notif_success(self,challenge,team,salon_name):
        """ Send notification of success of challenge for team in salon.annonces """
        salon = get(self.bot.get_guild(GUILD_ID).categories,name=salon_name)
        if salon is None:
            logger.warning(f"Category {salon} for challenge {challenge} not found !!")
        chan = get(salon.channels,name="koth")
        if chan is None:
            logger.warning(f"Chan koth of {salon} for challenge {challenge} not found !!")
            return
        async for message in chan.history():
            if team["name"]  in message.content and challenge['name'] in message.content:
                return
        await chan.send(f"La team **{team['name']}** (*{','.join(x.split('#')[0] for x in team['membres'])}*) a résolu **{challenge['name']}** le {datetime.fromisoformat(challenge['date']).strftime('%d/%m/%y à %H:%M')}")


    async def create_chan(self,chal):
        """
            Create category and channels for chal_name
        """
        chal_name = chal['name']
        logger.debug(f"create_chan {chal_name}")
        guild = self.bot.get_guild(GUILD_ID)
        salon_name, chan_name, role_name = challenge_to_SCR(chal_name)
        if salon_name is None:
            logger.warning(f"Can not parse {chal_name} !!")
            return

        role = get(guild.roles,name=role_name)
        if role is None:
            logger.info(f"Creating role {role_name} for {chal_name}")
            role = await guild.create_role(name=role_name)
        salon = get(guild.categories,name=salon_name)

        if salon is None:
            logger.info(f"Creating category  {salon_name} for {chal_name}")
            salon = await guild.create_category(salon_name,position=len(guild.categories))
            overwrites = {guild.default_role:discord.PermissionOverwrite(send_messages=False)}
            koth = await salon.create_text_channel('koth',overwrites=overwrites)
            await salon.create_text_channel("discussion")
        
        chan = get(salon.channels,name=chan_name)
        if chan is None:
            logger.info(f"Creating chan {chan_name} for {chal_name}")
            html = urljoin(CTFD_SITE.rstrip("/")+"/",f"challenges#{chal_name.replace(' ','%20')}-{chal['id']}")
            chan = await salon.create_text_channel(chan_name,topic=html+f"  (*{chal['value']} points *)")
            msg = await chan.send(chal["description"])
            await msg.pin()

        chan_success = get(salon.channels,name=chan_name+"-success")
        if chan_success is None:
            logger.info(f"Creating chan {chan_name}-success for {chal_name}")
            overwrites = {
                            guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            role : discord.PermissionOverwrite(read_messages=True)
            }
            html = urljoin(CTFD_SITE.rstrip("/")+"/",
                           f"challenges#{chal_name.replace(' ','%20')}-{chal['id']}")
            chan_success = await salon.create_text_channel(chan_name+"-success", overwrites=overwrites, topic=html+f"  (*{chal['value']} points *)")

    

    async def give_role(self,role_name,discord_nick):
        """ 
            Give the role role_name to discord_nick
        """
        member = self.bot.get_guild(GUILD_ID).get_member_named(discord_nick)
        if member is None:
            logger.warning(f"Error ctfdapi : user not found : {discord_nick} in {GUILD_ID}")
            return 
        role = get(self.bot.get_guild(GUILD_ID).roles,name=role_name)
        if role is None:
            logger.warning(f"Error Role not found : {role_name} in {GUILD_ID}")
        if role not in member.roles:
            logger.info(f"Giving {role_name} to {discord_nick}")
            await member.add_roles(role)
        

    @commands.command("pwd")
    @commands.dm_only()
    async def reset_pwd(self,ctx,pwd):
        discord_nick,tag = ctx.author.name,ctx.author.discriminator
        user = [u for u in self.link.get_users() if u["discord_nick"]==f"{discord_nick}#{tag}"]
        if len(user)==0:
            logger.info(f"Reset pwd : Utilisateur {discord_nick}#{tag} inconnu sur {CTFD_SITE}")
            await ctx.send(f"Utilisateur {discord_nick}#{tag} inconnu sur {CTFD_SITE}")
            return
        user = user[0]
        if not self.link.reset_pwd(user,pwd):
            await ctx.send(f"Mot de passe non changé.")
            return
        await ctx.send(f"Mot de passe changé")

    @commands.command("teampwd")
    @commands.dm_only()
    async def reset_team_pwd(self,ctx,pwd):
        def _find_team_of_user(teams,discord_nick):
            for t in teams:
                tmp = [u for u in t["membres"] if u['discord_nick']==discord_nick]
                if len(tmp)>0:
                    return t,tmp[0]
            return None
        discord_nick,tag = ctx.author.name,ctx.author.discriminator
        team, user = _find_team_of_user(self.link.get_teams(),f"{discord_nick}#{tag}")
        if team["captain_id"] != user['id']:
            await ctx.send("Seul le capitaine peut changer le mot de passe !")
            return 
        if not self.link.reset_team_pwd(team,pwd):
            await ctx.send(f"Mot de passe non changé.")
            return
        await ctx.send(f"Mot de passe changé")



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


        req = self.session.patch(f"teams/{team['id']}",json=data)
        if req.status_code != 200:
            logger.error(f"Error patch team_pwd {req.url} {req.status_code}")
            return False
        if not req.json()["success"]:
            logger.error(
                f"Error patch team_pwd {req.url} {req.json()['errors']}")
            return False
        return True


def _treat_req(req):
    if req.status_code != 200:
        logger.error(f"Error {req.url} {req.status_code}")
        return None
    if not req.json()["success"]:
        logger.error(f"Error json {req.url} {req.json()['errors']}")
        return None
    return req.json()["data"]


def _date_after(date,timestamp):
    return datetime.fromisoformat(date).astimezone() > datetime.fromtimestamp(timestamp).astimezone() 


def _format_user(u):
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
    salon = salon.strip().replace(" ","-").lower()
    chan = chan.strip().replace(" ","-").replace("#","-").lower()
    role = salon.lower()+"-"+chan
    return salon,chan,role

def generate_session():
    s = APISession(prefix_url=CTFD_SITE)
    s.headers.update({"Authorization": f"Token {CTFD_TOKEN}"})
    return s


def setup(bot):
    bot.add_cog(CTFDnotif(bot))
