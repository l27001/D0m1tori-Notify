#!/usr/bin/python3
### Script for sending messages
import requests, sys, time, random, os, json, builtins
from datetime import datetime
from string import ascii_letters
from config import vk_info, user_token, tmp_dir
import methods as Methods
dir_path = os.path.dirname(os.path.realpath(__file__))

def check_stream(id_):
    headers = Methods.twitch_api_auth()
    try:
        info = requests.get("https://api.twitch.tv/helix/streams", headers=headers, params={'user_id':id_, 'first':1}).json()['data'][0]
    except IndexError:
        return {"error":"Стрим не запущен"}
    streamer = requests.get("https://api.twitch.tv/helix/channels", params={'broadcaster_id': id_}, headers=headers).json()['data'][0]
    img = info['thumbnail_url'][:info['thumbnail_url'].find('{')-1] + info['thumbnail_url'][info['thumbnail_url'].rfind('}')+1:] + "?d0m_id=" + str(''.join(random.choice(ascii_letters) for i in range(12)))
    if(not os.path.isdir(tmp_dir)):
        os.mkdir(tmp_dir)
    img_name = f"{tmp_dir}/preview.{img.split('.')[-1]}"
    Methods.download_img(img, img_name)
    txt = f"Стрим начался, бегом смотреть!\n{info['game_name']} | {info['title']}\n"
    link = f"https://twitch.tv/{streamer['broadcaster_login']}"
    data = {'img_local': img_name, 'img_link':img, 'txt':txt, 'link':link}
    return data

def send_vk(img_name, txt, link='', post=True, rass=True):
    Mysql = Methods.Mysql()
    Vk = Methods.Vk()
    if(img_name):
        img = Vk.upload_img(331465308, img_name)
    else: img = ''
    if(post == True):
        try:
            response = requests.get("https://api.vk.com/method/wall.post",
                params={'access_token': user_token,
                        'v': '5.131',
                        'owner_id': f"-{vk_info['groupid']}",
                        'from_group': 1,
                        'attachments': link,
                        'message': txt+link
                        }).json()
        except Exception as e:
            print("fail wall.post")
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
                Vk.send(peer_id=a,message=txt+link,attachment=img,mass=True)
                i+=50
                time.sleep(0.2)
        except Exception as e:
            print("Vk chat send error")


        try:
            rass = Mysql.query("SELECT COUNT(vkid) FROM `users` WHERE notify='1'")
            i = 0
            while i < rass['COUNT(vkid)']:
                a = []
                r = Mysql.query(f"SELECT vkid FROM `users` WHERE notify='1' LIMIT {i}, 50", fetch="all")
                for n in r:
                    a.append(str(n['vkid']))
                a = ",".join(a)
                Vk.send(peer_id=a,message=txt+link,attachment=img,mass=True)
                i+=50
                time.sleep(0.2)
        except Exception as e:
            print("Vk user send error")
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
            print("Error discord send")
    Mysql.close()

def send_tg(txt, link=""):
    Tg = Methods.Tg()
    Mysql = Methods.Mysql()
    users = Mysql.query("SELECT tgid FROM tg_users WHERE subscribe=1", fetch="all")
    for user in users:
        try:
            Tg.sendMessage(user['tgid'], txt+link)
        except:
            print("ERROR", f"Error Tg.sendMessage to user {user['tgid']}")
    chats = Mysql.query("SELECT id FROM tg_chats WHERE subscribe=1", fetch="all")
    for chat in chats:
        try:
            Tg.sendMessage(chat['id'], txt+link)
        except:
            print("ERROR", f"Error Tg.sendMessage to chat {chat['id']}")
    Mysql.close()

if(__name__ == "__main__"):
    id_ = sys.argv[1]
    data = check_stream(id_)
    if('error' in data):
        print(data['error'])
        exit()
    send_vk(data['img_local'], data['txt'], data['link'])
    send_ds(data['img_link'], data['txt'], data['link'])
    send_tg(data['txt'], data['link'])
    os.remove(data['img_local'])
