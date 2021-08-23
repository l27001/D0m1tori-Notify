#!/usr/bin/python3
import requests, sys, time, random, os, json
from datetime import datetime
from webhook import twitch_api_auth
from config import groupid, user_token
from methods import Methods
dir_path = os.path.dirname(os.path.realpath(__file__))

def check_stream(id_):
    headers = twitch_api_auth()
    # id_ = requests.get("https://api.twitch.tv/helix/users?login=godenname", headers=headers).json()['data'][0]['id']
    try:
        info = requests.get("https://api.twitch.tv/helix/streams", headers=headers, params={'user_id':id_, 'first':1}).json()['data'][0]
    except IndexError:
        return {"error":"Стрим не запущен"}
    streamer = requests.get("https://api.twitch.tv/helix/channels", params={'broadcaster_id': id_}, headers=headers).json()['data'][0]
    # Can use: info['title'], info['game_name'], info['user_name'], info['thumbnail_url'], info['started_at'], info['viewer_count']
    img = info['thumbnail_url'][:info['thumbnail_url'].find('{')-1] + info['thumbnail_url'][info['thumbnail_url'].rfind('}')+1:]
    img_name = f"{dir_path}/preview.{img.split('.')[-1]}"
    Methods.download_img(img, img_name)
    txt = f"Стрим начался, бегом смотреть!\n{info['game_name']} | {info['title']}\n"
    link = f"https://twitch.tv/{streamer['broadcaster_login']}"
    data = {'img_local': img_name, 'img_link':img, 'txt':txt, 'link':link}
    return data

def send_vk(img_name, txt, link='', post=True, rass=True):
    Mysql = Methods.Mysql()
    if(img_name):
        img = Methods.upload_img(331465308, img_name)
    else: img = ''
    if(post == True):
        try:
            response = requests.get("https://api.vk.com/method/wall.post",
                params={'access_token': user_token,
                        'v': '5.131',
                        'owner_id': f"-{groupid}",
                        'from_group': 1,
                        'attachments': link,
                        'message': txt+link
                        }).json()
        except Exception as e:
            Methods.send(331465308, f"send.py: fail wall.post\n{e}")
    if(rass == True):
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
                time.sleep(0.2)
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
                time.sleep(0.2)
        except Exception as e:
            Methods.send(331465308, f"send.py: fail users.send\n{e}")
    Mysql.close()

def send_ds(img, txt, link, custom=False):
    Mysql = Methods.Mysql()
    guilds = Mysql.query("SELECT * FROM webhooks WHERE enabled = 1", fetch="all")
    now = datetime.now().strftime("%H:%M %d.%m.%Y")
    headers = {
        'Content-Type': 'application/json'
    }
    if(custom == False):
        data = {
            "content": "@everyone",
            "username": "D0m1tori Notify",
            "embeds": [
            {
              "title": "Стрим начался, бегом смотреть!",
              "color": 16736768,
              "description": f"**{txt}**",
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
                  "url": link
                }
              ]
            }
          ]
        }
    else:
        data = {
            "content": "@everyone\n"+txt,
            "username": "D0m1tori Notify",
        }
    for guild in guilds:
        try:
            r = requests.post(guild['link']+"?wait=true", data=json.dumps(data), headers=headers)
            if(r.status_code != 204):
                rdata = r.json()
                if('code' in rdata and rdata['code'] == 10015):
                    Mysql.query("DELETE FROM webhooks WHERE id = %s", (guild['id']))
                elif('code' in rdata):
                    print(rdata)
        except:
            Methods.send(331465308, f"send.py: fail discord.send\n{e}")
    Mysql.close()

if(__name__ == "__main__"):
    id_ = sys.argv[1]
    data = check_stream(id_)
    if('error' in data):
        print(data['error'])
        exit()
    send_vk(data['img_local'], data['txt'], data['link'])
    send_ds(data['img_link'], data['txt'], data['link'])
    os.remove(data['img_local'])
