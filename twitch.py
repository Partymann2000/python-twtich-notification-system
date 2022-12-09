import discord
import json
import asyncio
import datetime
import requests
import time

from discord.ext import commands, tasks
from datetime import datetime, date, time, timezone, timedelta

with open("config.json") as config_file:
    config = json.load(config_file)

def get_app_access_token():
    params = {
        "client_id": config["twitch"]["client_id"],
        "client_secret": config["twitch"]["client_secret"],
        "grant_type": "client_credentials"
    }

    response = requests.post("https://id.twitch.tv/oauth2/token", params=params)
    access_token = response.json()["access_token"]
    return access_token

# Berechne die UNIX Zeit für 60 Tage in der Zukunft in diesem format: <t:UNIXTIME:R
def unix_time():
    now = datetime.now()
    future = now + timedelta(weeks=3)
    unix_time = future.timestamp()
    return int(unix_time)

def get_users(login_names):
    params = {
        "login": login_names
    }

    headers = {
        "Authorization": "Bearer {}".format(config["twitch"]["access_token"]),
        "Client-Id": config["twitch"]["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/users", params=params, headers=headers)
    return {entry["login"]: entry["id"] for entry in response.json()["data"]}

def get_streams(users):
    params = {
        "user_id": users.values()
    }

    headers = {
        "Authorization": "Bearer {}".format(config["twitch"]["access_token"]),
        "Client-Id": config["twitch"]["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/streams", params=params, headers=headers)
    return {entry["user_login"]: entry for entry in response.json()["data"]}


online_users = {}


def get_notifications():
    users = get_users(config["twitch"]["watchlist"])
    streams = get_streams(users)

    notifications = []
    for user_name in config["twitch"]["watchlist"]:
        if user_name not in online_users:
            online_users[user_name] = datetime.utcnow()

        if user_name not in streams:
            online_users[user_name] = None
        else:
            started_at = datetime.strptime(streams[user_name]["started_at"], "%Y-%m-%dT%H:%M:%SZ")
            if online_users[user_name] is None or started_at > online_users[user_name]:
                notifications.append(streams[user_name])
                online_users[user_name] = started_at

    return notifications

class twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_twitch_online_streamers.start()
        self.check_twitch_access_token.start()

    @tasks.loop(seconds=60)
    async def check_twitch_access_token(self):
        print("Access token is checked")
        time = datetime.now()
        current_time = time.timestamp()
        if int(current_time) >= config["twitch"]["expire_date"]:
            access_token = get_app_access_token()
            config["twitch"]["access_token"] = access_token
            config["twitch"]["expire_date"] = unix_time()
            print("The access token was regenerated")
            with open("config.json", "w") as config_file:
                json.dump(config, config_file, indent=4)

    @tasks.loop(seconds=90)
    async def check_twitch_online_streamers(self):
        channel = self.bot.get_channel(config["twitch"]["channel_id"])
        if not channel:
            return

        notifications = get_notifications()
        for notification in notifications:
            game = "{}".format(notification["game_name"])
            if game == "":
                embed=discord.Embed(title="{}".format(notification["title"]), url="https://twitch.tv/{}".format(notification["user_login"]), description="[Watch](https://twitch.tv/{})".format(notification["user_login"]), color=0x001eff)
                embed.set_author(name="{} Stream ist jetzt Live".format(notification["user_name"]), url="https://twitch.tv/{}".format(notification["user_login"]))
                embed.add_field(name="Game", value="Unbekannt", inline=True)
                embed.add_field(name="Viewers", value="{}".format(notification["viewer_count"]), inline=True)
                embed.set_image(url="https://static-cdn.jtvnw.net/previews-ttv/live_user_{}-1920x1080.jpg?time=1526732772".format(notification["user_login"]))
                await channel.send(embed=embed)
            else:
                embed=discord.Embed(title="{}".format(notification["title"]), url="https://twitch.tv/{}".format(notification["user_login"]), description="[Watch](https://twitch.tv/{})".format(notification["user_login"]), color=0x001eff)
                embed.set_author(name="{} Stream ist jetzt Live".format(notification["user_name"]), url="https://twitch.tv/{}".format(notification["user_login"]))
                embed.add_field(name="Game", value="-{}".format(notification["game_name"]), inline=True)
                embed.add_field(name="Viewers", value="{}".format(notification["viewer_count"]), inline=True)
                embed.set_image(url="https://static-cdn.jtvnw.net/previews-ttv/live_user_{}-1920x1080.jpg?time=1526732772".format(notification["user_login"]))
                await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(twitch(bot))
