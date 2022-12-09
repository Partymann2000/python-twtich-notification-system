# Python Twitch Notification System

## About

This is a Python script that can be used in a cog. This script will send you in your Discord a Twitch notification from people you can define in a config, you can also choose a channel where you want to send the notification and a role you want to tag.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install asyncio, py-cord, requests
```

## Usage

### 1. ClientID and the ClientSecret

### STEP 1.1
Go to the following website [Twitch Developer Portal](https://dev.twitch.tv/) and `log in`. After logging in, click on `Your Console` in the upper right corner next to your profile picture.

### STEP 1.2
Under the heading Console you will find a category called `Applications`, select it and press `Register your application`.

### STEP 1.3
At `OAuth Redirect URLs` you enter `https://localhost`, at Category you select Other, now you confirm that you are a robot. Now go to more details and enter what you want to do with the API. `(for example: Create a Discord Notification System)` Now click on `Create`

### STEP 1.4
Now you see your current applications, you press `Manage` on your application

###´STEP 1.5
Now you can find your `client ID` at the bottom. To create a new `client secret`, click on `new secret` and there you will now see your `client secret`

### 2. The Code

### 2.1
The script is a cog and therefore must be placed in a `cog directory`

```python
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
```

### 2.2
The next one is a part of a `config` and has to be added to your `config.json` or you just take the file from here (just put it into the directory where the `main.py` is)

```json
{
	"twitch": {
		"client_id": "xxx",
		"client_secret": "xxx",
		"access_token": "xxx",
        	"channel_id": xxx,
        	"expire_date": 1669483138,
		"watchlist": [
			"partymann2000hd",
			"BastiGHG",
			"bonjwa",
		    "chrisfigge",
		    "artimus83",
		    "dennsen86",
		    "achnina",
		    "Trymacs",
		    "VarsityGaming",
		    "MontanaBlack88",
		    "unsympathisch_tv",
		    "Papaplatte",
		    "TheRealOnit",
		    "GronkhTV",
		    "maxikingg88"
		]
	}
}
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[Xenority](https://discord.gg/rvJeT9sm82)
