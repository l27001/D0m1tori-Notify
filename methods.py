import re, requests, datetime, os, random, time, pymysql, pymysql.cursors
from pymysql.err import InterfaceError, OperationalError
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
from OpenSSL.SSL import Error as VeryError
import config

headers = {
    'User-Agent': "D0m1toriBot/Methods"
}

class Mysql:

    def __init__(self):
        self.con = Mysql.make_con()

    def query(self,query,variables=(),fetch="one"):
        try:
            cur = self.con.cursor()
            cur.execute(query, variables)
        except (InterfaceError,OperationalError):
            self.con = Mysql.make_con()
            cur = self.con.cursor()
            cur.execute(query, variables)
        if(fetch == "one"):
            data = cur.fetchone()
        else:
            data = cur.fetchall()
        return data

    def make_con(self=None):
        return pymysql.connect(host=config.db['host'],
                 user=config.db['user'],
                 password=config.db['password'],
                 db=config.db['database'],
                 charset='utf8mb4',
                 autocommit=True,
                 cursorclass=pymysql.cursors.DictCursor)

    def close(self):
        self.con.close()

class Vk:

    def __init__(self, token=config.vk_info['access_token'], lang="ru", v="5.124"):
        self.params = {"access_token":token,"lang":lang,"v":v}
        self.url = config.vk_info['url']

    def getLongPollServer(self, update_ts=True):
        params = self.getRequestParams({'group_id': config.vk_info['groupid']})
        response = requests.get(self.url+"groups.getLongPollServer", params=params).json()['response']
        self.key = response['key']
        self.server = response['server']
        if(update_ts == True): self.ts = response['ts']

    def updateParams(self, key=None, server=None, ts=None):
        if(key != None):
            self.key = key
        if(server != None):
            self.server = server
        if(ts != None):
            self.ts = ts

    def getRequestParams(self, new_params):
        params = self.params
        params.update(new_params)
        return params

    def getTS(self):
        return self.ts
    
    def getMessages(self):
        try:
            response = requests.get(f"{self.server}?act=a_check&key={self.key}&ts={self.ts}&wait=60",
                timeout=61)
            return response.json()
        except(VeryError, ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
            print("WARN","Сервер не ответил. Жду 3 секунды перед повтором.")
            time.sleep(3)

    def make_button(self,color="primary",type_="text",**kwargs):
        a = []
        for name,data in kwargs.items():
            a.append('"'+name+'":"'+str(data)+'"')
        kk = ",".join(a)
        if(type_ != "intent_unsubscribe" and type_ != "intent_subscribe"):
            return"{\"color\":\""+color+"\",\"action\":{\"type\":\""+type_+"\","+kk+"}}"
        else:
            return"{\"action\":{\"type\":\""+type_+"\","+kk+"}}"

    def construct_keyboard(self,inline="false",one_time="false",**kwargs):
        a = []
        for n in kwargs:
            a.append("["+kwargs[n]+"]")
        kx = f'"buttons":{a},"inline":{inline},"one_time":{one_time}'
        kx = '{'+kx+'}'
        return re.sub(r"[']",'',kx)

    def users_get(self, user_id, fields=''):
        params = self.getRequestParams({"user_ids":user_id, "fields": fields})
        response = requests.get(f"{self.url}users.get", params=params)
        return response.json()['response']

    def send(self,peer_id,message='',attachment='',keyboard='{"buttons":[]}',disable_mentions=0,intent="default",mass=False):
        if(mass == True):
            params = self.getRequestParams({"peer_ids":peer_id, "random_id":random.randint(1,2147400000), "message":message, "attachment":attachment, "keyboard":keyboard, "disable_mentions":disable_mentions, "intent":intent})
        else:
            params = self.getRequestParams({"peer_id":peer_id, "random_id":random.randint(1,2147400000), "message":message, "attachment":attachment, "keyboard":keyboard, "disable_mentions":disable_mentions, "intent":intent})
        response = requests.get(f"{self.url}messages.send", params=params).json()
        return response

    def is_message_allowed(self, id_):
        params = self.getRequestParams({"user_id":id_, "group_id":config.vk_info['groupid']})
        response = requests.get(f"{self.url}messages.isMessagesFromGroupAllowed", params=params)
        return response.json()['response']['is_allowed']

    def check_keyboard(self, inline):
        if(inline):
            return "true"
        else:
            return "false"

    def getById(self, id_):
        params = self.getRequestParams({"group_id": id_})
        response = requests.get(f"{self.url}groups.getById", params=params)
        return response.json()['response']

    def upload_img_msg(self, peer_id, file):
        if(self.is_message_allowed(peer_id) == 1):
            params = self.getRequestParams({"peer_id":peer_id})
        else:
            params = self.getRequestParams({"peer_id":331465308})
        srvv = requests.get(f"{self.url}photos.getMessagesUploadServer", params=params).json()['response']['upload_url']
        no = requests.post(srvv, files={
                    'file': open(file, 'rb')
                }).json()
        if(no['photo'] == '[]'):
            return 1
        params = self.getRequestParams({"photo":no['photo'],"server":no['server'],"hash":no['hash']})
        response = requests.get(f"{self.url}photos.saveMessagesPhoto", params=params).json()['response']
        return f"photo{response[0]['owner_id']}_{response[0]['id']}_{response[0]['access_key']}"

    ### /start/ old api zone
    # def upload_voice(peer_id,file):
    #     if(Methods.is_message_allowed(peer_id) == 1):
    #         url = api.docs.getMessagesUploadServer(type='audio_message',peer_id=peer_id)['upload_url']
    #     else:
    #         url = api.docs.getMessagesUploadServer(type='audio_message',peer_id=331465308)['upload_url']
    #     file = requests.post(url, files={
    #                 'file': open(file, 'rb')
    #             }).json()['file']
    #     file = api.docs.save(file=file)
    #     return f"doc{file['audio_message']['owner_id']}_{file['audio_message']['id']}_{file['audio_message']['access_key']}"

    # def get_conversation_members(peer_id):
    #     try:
    #         return api.messages.getConversationMembers(group_id=config.vk_info['groupid'],peer_id=peer_id)['items']
    #     except Exception as e:
    #         if(e.code == 917):
    #             return 917

    # def check_name(name):
    #     return api.utils.resolveScreenName(screen_name=name)

    # def kick_user(chat,name):
    #     api.messages.removeChatUser(chat_id=chat-2000000000,member_id=name)

    # def del_message(message_ids,delete_for_all=1,group_id=config.vk_info['groupid']):
    #     return api.messages.delete(message_ids=message_ids,delete_for_all=1,group_id=config.vk_info['groupid'])

    # def set_typing(peer_id,type_='typing',group_id=config.vk_info['groupid']):
    #     api.messages.setActivity(group_id=config.vk_info['groupid'],peer_id=peer_id,type=type_)
    ### /end/ old api zone

class Tg:

    def __init__(self, token=config.tg_info['access_token']):
        self.url = f"{config.tg_info['url']}bot{token}/"
        self.offset = 0
        self.getMe()

    def getOffset(self):
        return self.offset

    def setOffset(self, offset):
        self.offset = offset

    def getUpdates(self, offset=0, timeout=60):
        data = requests.get(f"{self.url}getUpdates", params={"offset":offset, "timeout":timeout}, timeout=61).json()
        if(len(data['result']) > 0):
            self.offset = data['result'][-1]['update_id']+1
        return data

    def sendMessage(self, chat_id, text, allow_sending_without_reply=True, parse_mode="Markdown", **kwargs):
        params = {"chat_id":chat_id, "text":text, "allow_sending_without_reply":allow_sending_without_reply, "parse_mode":parse_mode}
        params.update(kwargs)
        data = requests.get(f"{self.url}sendMessage", params=params)
        return data.json()

    def sendPhoto(self, chat_id, photo, **kwargs):
        params = {"chat_id":chat_id, "photo":photo}
        params.update(kwargs)
        data = requests.get(f"{self.url}sendPhoto", params=params)
        return data.json()

    def getMe(self):
        data = requests.get(f"{self.url}getMe").json()['result']
        self.id = data['id']
        self.username = data['username']

def download_img(url, file):
    p = requests.get(url, headers=headers)
    with open(file, "wb") as out:
        out.write(p.content)
    return file

def twitch_api_auth():
    Mysql_ = Mysql()
    now = datetime.datetime.now().timestamp()
    auth = Mysql_.query("SELECT * FROM twitch_api_key WHERE `not-after`>%s LIMIT 1", (now))
    if(auth == None):
        data = {
            'client_id': config.client_id,
            'client_secret': config.twitch_api,
            'grant_type': "client_credentials"
        }
        auth = requests.post(f"https://id.twitch.tv/oauth2/token", headers=headers, data=data, proxies=config.proxies).json()
        Mysql_.query("DELETE FROM twitch_api_key")
        Mysql_.query("INSERT INTO twitch_api_key (`key_`, `not-after`, `type`, `client_id`) VALUES (%s, %s, %s, %s)", (auth['access_token'], now+auth['expires_in'], auth['token_type'], config.client_id))
        headers.update({
            'Authorization': f"{auth['token_type'].title()} {auth['access_token']}",
            'Client-Id': config.client_id,
        })
    else:
        headers.update({
            'Authorization': f"{auth['type'].title()} {auth['key_']}",
            'Client-Id': auth['client_id'],
            })
    headers.update({'Content-Type': "application/json"})
    Mysql_.close()
    return headers

def check_stream():
    headers = twitch_api_auth()
    params = {'user_login': config.streamer_info['id'], 'first': 1}
    response = requests.get("https://api.twitch.tv/helix/streams", params=params, headers=headers, proxies=config.proxies).json()
    if(response['data'] == []):
        return "Сейчас трансляция не ведётся."
    else:
        response = response['data'][0]
        return f"Название: {response['title']}\n\
            Игра: {response['game_name']}\n\
            Зрителей: {response['viewer_count']}\n\
            https://twitch.tv/{response['user_login']}"
