#!/usr/bin/python3
from webhook import twitch_api_auth
from config import groupid, user_token
from methods import Methods
import requests, sys, time, random, os
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
        rass = Methods.mysql_query("SELECT COUNT(id) FROM `chats` WHERE notify='1'")
        i = 0
        while i < rass['COUNT(id)']:
            a = []
            r = Methods.mysql_query(f"SELECT id FROM `chats` WHERE notify='1' LIMIT {i}, 50", fetch="all")
            for n in r:
                a.append(str(n['id']))
            a = ",".join(a)
            Methods.mass_send(peer_ids=a,message=txt+link,attachment=img)
            i+=50
            time.sleep(1)
    except Exception as e:
        Methods.send(331465308, f"send.py: fail chats.send\n{e}")

    try:
        rass = Methods.mysql_query("SELECT COUNT(vkid) FROM `users` WHERE notify='1'")
        i = 0
        while i < rass['COUNT(vkid)']:
            a = []
            r = Methods.mysql_query(f"SELECT vkid FROM `users` WHERE notify='1' LIMIT {i}, 50", fetch="all")
            for n in r:
                a.append(str(n['vkid']))
            a = ",".join(a)
            Methods.mass_send(peer_ids=a,message=txt+link,attachment=img)
            i+=50
            time.sleep(1)
    except Exception as e:
        Methods.send(331465308, f"send.py: fail users.send\n{e}")

def send_ds():
    guilds = Methods.mysql_query("SELECT * FROM webhooks WHERE enabled = 1", fetch="all")
    with open(img_name ,'rb') as f:
        fdata = f.read()
    headers = {
        # 'Content-Type': 'multipart/form-data'
    }
    files = {}
    data = {
        'content': '@everyone\n'+txt+link,
    }
    for guild in guilds:
        try:
            r = requests.post(guild['link']+"?wait=true", files=files, data=data, headers=headers)
            if(r.status_code != 204):
                rdata = r.json()
                if('code' in rdata and rdata['code'] == 10015):
                    Methods.mysql_query("DELETE FROM webhooks WHERE id = %s", (guild['id']))
                else:
                    print(rdata)
        except:
            Methods.send(331465308, f"send.py: fail discord.send\n{e}")

if(__name__ == "__main__"):
    send_vk()
    send_ds()
    os.remove(img_name)