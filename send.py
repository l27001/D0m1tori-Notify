#!/usr/bin/python3
### Script for sending messages
import requests, sys, time, random, os, json, builtins
from datetime import datetime
from string import ascii_letters
from config import vk_info, user_token, tmp_dir, proxies
import methods as Methods
dir_path = os.path.dirname(os.path.realpath(__file__))

def check_stream(id_):
    id_ = int(id_)
    headers = Methods.twitch_api_auth()
    try:
        info = requests.get("https://api.twitch.tv/helix/streams", timeout=30, headers=headers, params={'user_id':id_}, proxies=proxies).json()['data'][0]
    except IndexError:
        return {"status":"warning", "description":"Трансляция сейчас не запущена"}
    except requests.exceptions.ReadTimeout:
        return {"status":"error", "description":"Превышено время ожидания ответа от Twitch API"}
    streamer = requests.get("https://api.twitch.tv/helix/channels", timeout=30, params={'broadcaster_id': id_}, headers=headers, proxies=proxies).json()['data'][0]
    img = info['thumbnail_url'][:info['thumbnail_url'].find('{')-1] + info['thumbnail_url'][info['thumbnail_url'].rfind('}')+1:] + "?d0m_id=" + str(''.join(random.choice(ascii_letters) for i in range(12)))
    if(not os.path.isdir(tmp_dir)):
        os.mkdir(tmp_dir)
    img_name = f"{tmp_dir}/preview.{img.split('.')[-1]}"
    Methods.download_img(img, img_name)
    txt = f"Стрим начался, бегом смотреть!\n{info['game_name']} | {info['title']}\n"
    link = f"https://twitch.tv/{streamer['broadcaster_login']}"
    data = {'status': "success", 'img_local': img_name, 'img_link':img, 'txt':txt, 'link':link}
    return data

def send_vk(img_name, txt, link='', post=True, rass=True):
    Mysql = Methods.Mysql()
    Vk = Methods.Vk()
    params = {
        'access_token': user_token,
        'v': '5.131'
    }
    if(img_name):
        # img to users/chats
        img = Vk.upload_img_msg(331465308, img_name)

        # img to Wall
        paramss = params
        paramss.update({"group_id":vk_info['groupid']})
        srvv = requests.get("https://api.vk.com/method/photos.getWallUploadServer", params=paramss).json()['response']['upload_url']
        no = requests.post(srvv, files={
                    'file': open(img_name, 'rb')
                }).json()
        if(no['photo'] not in ['[]','']):
            paramss = params
            paramss.update({"group_id":vk_info['groupid'],"photo":no['photo'],"server":no['server'],"hash":no['hash']})
            response = requests.get("https://api.vk.com/method/photos.saveWallPhoto", params=params).json()['response']
            attach = f"photo{response[0]['owner_id']}_{response[0]['id']}_{response[0]['access_key']}"
        else: attach = ''
    else: img = ''; attach = ''
    if(post == True):
        try:
            response = requests.get("https://api.vk.com/method/wall.post",
                params={'access_token': user_token,
                        'v': '5.131',
                        'owner_id': f"-{vk_info['groupid']}",
                        'from_group': 1,
                        'attachments': attach+link,
                        'message': txt+link
                        }, timeout=30).json()
        except Exception as e:
            print("fail wall.post")
    if(rass == True):
            rass = Mysql.query("SELECT COUNT(id) FROM vk_subscribe WHERE subscribe=1")
            i = 0
            while i < rass['COUNT(id)']:
                try:
                    a = []
                    r = Mysql.query(f"SELECT id FROM vk_subscribe WHERE subscribe=1 LIMIT {i}, 50", fetch="all")
                    for n in r:
                        a.append(str(n['id']))
                    a = ",".join(a)
                    Vk.send(peer_id=a,message=txt+link,attachment=img,mass=True)
                    i+=50
                    time.sleep(0.2)
                except Exception as e:
                    print("Vk send error")
                    print(a, i)
    Mysql.close()

def send_ds(img, txt, link, custom=False):
    Mysql = Methods.Mysql()
    guilds = Mysql.query("SELECT * FROM webhook WHERE enabled = 1", fetch="all")
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
            r = requests.post(guild['link']+"?wait=true", data=json.dumps(data), headers=headers, timeout=30)
            if(r.status_code != 204):
                rdata = r.json()
                if('code' in rdata and rdata['code'] == 10015):
                    Mysql.query("DELETE FROM webhook WHERE id = %s", (guild['id']))
                elif('code' in rdata):
                    print(rdata)
        except:
            print("Error discord send")
    Mysql.close()

def send_tg(txt, link=""):
    Tg = Methods.Tg()
    Mysql = Methods.Mysql()
    subs = Mysql.query("SELECT id FROM tg_subscribe WHERE subscribe=1", fetch="all")
    for subscriber in subs:
        try:
            Tg.sendMessage(subscriber['id'], txt+link)
        except:
            print("ERROR", f"Error Tg.sendMessage to {subscriber['id']}")
    Mysql.close()

if(__name__ == "__main__"):
    id_ = sys.argv[1]
    data = check_stream(id_)
    if(data['status'] != "success"):
        print(data['description'])
        exit()
    send_vk(data['img_local'], data['txt'], data['link'])
    send_ds(data['img_link'], data['txt'], data['link'])
    send_tg(data['txt'], data['link'])
    os.remove(data['img_local'])
