#!/usr/bin/python3
import requests, sys, time, random, os, json
from datetime import datetime
from webhook import twitch_api_auth
from config import groupid, user_token
from methods import Methods
dir_path = os.path.dirname(os.path.realpath(__file__))
id_ = sys.argv[1]
headers = twitch_api_auth()
# id_ = requests.get("https://api.twitch.tv/helix/users?login=godenname", headers=headers).json()['data'][0]['id']
info = requests.get("https://api.twitch.tv/helix/streams", headers=headers, params={'user_id':id_, 'first':1}).json()['data'][0]
streamer = requests.get("https://api.twitch.tv/helix/channels", params={'broadcaster_id': id_}, headers=headers).json()['data'][0]
# Can use: info['title'], info['game_name'], info['user_name'], info['thumbnail_url'], info['started_at'], info['viewer_count']
img = info['thumbnail_url'][:info['thumbnail_url'].find('{')-1] + info['thumbnail_url'][info['thumbnail_url'].rfind('}')+1:]
# print(img)
# exit()
img_name = f"{dir_path}/preview.{img.split('.')[-1]}"
Methods.download_img(img, img_name)
txt = f"Стрим начался, бегом смотреть!\n{info['title']}"
link = f"\nhttps://twitch.tv/{streamer['broadcaster_login']}"

def send_vk():
    img = Methods.upload_img(331465308, img_name)
    try:
        response = requests.get("https://api.vk.com/method/wall.post",
            params={'access_token': user_token,
                    'v': '5.131',
                    'owner_id': f"-{groupid}",
                    'from_group': 1,
                    'attachments': f"https://twitch.tv/{streamer['broadcaster_login']}",
                    'message': txt+link
                    }).json()
    except Exception as e:
        Methods.send(331465308, f"send.py: fail wall.post\n{e}")

    try:
        rass = Mysql.query("SELECT COUNT(id) FROM `chats` WHERE notify='1'")
        i = 0
        while i < rass['COUNT(id)']:
            a = []
            r = Mysql.query(f"SELECT id FROM `chats` WHERE notify='1' LIMIT {i}, 50", fetch="all")
            for n in r:
                a.append(str(n['id']))
            a = ",".join(a)
            Methods.mass_send(peer_ids=a,message=txt+link,attachment=img)
            i+=50
            time.sleep(1)
    except Exception as e:
        Methods.send(331465308, f"send.py: fail chats.send\n{e}")

    try:
        rass = Mysql.query("SELECT COUNT(vkid) FROM `users` WHERE notify='1'")
        i = 0
        while i < rass['COUNT(vkid)']:
            a = []
            r = Mysql.query(f"SELECT vkid FROM `users` WHERE notify='1' LIMIT {i}, 50", fetch="all")
            for n in r:
                a.append(str(n['vkid']))
            a = ",".join(a)
            Methods.mass_send(peer_ids=a,message=txt+link,attachment=img)
            i+=50
            time.sleep(1)
    except Exception as e:
        Methods.send(331465308, f"send.py: fail users.send\n{e}")

def send_ds():
    guilds = Mysql.query("SELECT * FROM webhooks WHERE enabled = 1", fetch="all")
    now = datetime.now().strftime("%H:%M %d.%m.%Y")
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "content": "@everyone",
        "username": "D0m1tori Notify",
        "embeds": [
        {
          "title": "Стрим начался, бегом смотреть!",
          "color": 16736768,
          "description": f"**{info['game_name']} | {info['title']}**",
          "author": {},
          "image": {
            "url": img
          },
          "thumbnail": {},
          "footer": {"text": now},
          "fields": []
        }
      ],
      "components": [
        {
          "type": 1,
          "components": [
            {
              "type": 2,
              "style": 5,
              "label": "Перейти на Twitch",
              "url": f"https://twitch.tv/{streamer['broadcaster_login']}"
            }
          ]
        }
      ]
    }
    for guild in guilds:
        try:
            r = requests.post(guild['link']+"?wait=true", data=json.dumps(data), headers=headers)
            if(r.status_code != 204):
                rdata = r.json()
                if('code' in rdata and rdata['code'] == 10015):
                    Mysql.query("DELETE FROM webhooks WHERE id = %s", (guild['id']))
                else:
                    print(rdata)
        except:
            Methods.send(331465308, f"send.py: fail discord.send\n{e}")

if(__name__ == "__main__"):
    Mysql = Methods.Mysql()
    send_vk()
    send_ds()
    os.remove(img_name)
    Mysql.close()