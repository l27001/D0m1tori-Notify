import re, requests, datetime, os, random, timeit, pymysql, pymysql.cursors
from pymysql.err import InterfaceError, OperationalError
import config

headers = {
    'User-Agent': "D0m1toriBot/Methods" # 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36 OPR/70.0.3728.133'
}

class Methods:

    def make_button(color="primary",type="text",**kwargs):
        a = []
        for name,data in kwargs.items():
            a.append('"'+name+'":"'+str(data)+'"')
        kk = ",".join(a)
        if(type != "intent_unsubscribe" and type != "intent_subscribe"):
            return"{\"color\":\""+color+"\",\"action\":{\"type\":\""+type+"\","+kk+"}}"
        else:
            return"{\"action\":{\"type\":\""+type+"\","+kk+"}}"

    def construct_keyboard(inline="false",one_time="false",**kwargs):
        a = []
        for n in kwargs:
            a.append("["+kwargs[n]+"]")
        kx = f'"buttons":{a},"inline":{inline},"one_time":{one_time}'
        kx = '{'+kx+'}'
        return re.sub(r"[']",'',kx)

    def log(prefix,message,timestamp=True):
        if(os.path.isdir(dir_path+"/log/") == False):
            os.mkdir(dir_path+"/log")
        file = dir_path+"/log/"+datetime.datetime.today().strftime("%d.%m.%Y")+".log"
        if(timestamp == True):
            message = f"({datetime.datetime.today().strftime('%H:%M:%S')}) [{prefix}] {message}"
        else:
            message = f"[{prefix}] {message}"
        print(message)
        with open(file, 'a', encoding='utf-8') as f:
            f.write(message+"\n")

    def users_get(user_id,fields=''):
        try:
            return api.users.get(user_ids=user_id,fields=fields)
        except:
            return api.users.get(user_ids=user_id,fields=fields)

    class Mysql:

        def __init__(self):
            self.con = Methods.Mysql.make_con()

        def query(self,query,variables=(),fetch="one",time=False):
            if(time == True):
                extime = timeit.default_timer()
            try:
                cur = self.con.cursor()
                cur.execute(query, variables)
            except (InterfaceError,OperationalError):
                self.con = Methods.Mysql.make_con()
                cur = self.con.cursor()
                cur.execute(query, variables)
            if(fetch == "one"):
                data = cur.fetchone()
            else:
                data = cur.fetchall()
            if(time == True):
                Methods.log("Debug",f"Время запроса к MySQL: {str(timeit.default_timer()-extime)}")
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

    def send(peer_id,message='',attachment='',keyboard='{"buttons":[]}',disable_mentions=0,intent="default"):
        return api.messages.send(peer_id=peer_id,random_id=random.randint(1,2147400000),message=message,attachment=attachment,keyboard=keyboard,disable_mentions=disable_mentions,intent=intent)

    def mass_send(peer_ids,message='',attachment='',keyboard='{"buttons":[]}',disable_mentions=0):
        return api.messages.send(peer_ids=peer_ids,random_id=random.randint(1,2147400000),message=message,attachment=attachment,keyboard=keyboard,disable_mentions=disable_mentions)

    def upload_img(peer_id, file):
        if(Methods.is_message_allowed(peer_id) == 1):
            srvv = api.photos.getMessagesUploadServer(peer_id=peer_id)['upload_url']
        else:
            srvv = api.photos.getMessagesUploadServer(peer_id=331465308)['upload_url']
        no = requests.post(srvv, files={
                    'file': open(file, 'rb')
                }).json()
        if(no['photo'] == '[]'):
            return 1
        response = api.photos.saveMessagesPhoto(photo=no['photo'],server=no['server'],hash=no['hash'])
        return f"photo{response[0]['owner_id']}_{response[0]['id']}_{response[0]['access_key']}"

    def download_img(url, file):
        p = requests.get(url, headers=headers)
        with open(file, "wb") as out:
            out.write(p.content)
        return file

    def upload_voice(peer_id,file):
        if(Methods.is_message_allowed(peer_id) == 1):
            url = api.docs.getMessagesUploadServer(type='audio_message',peer_id=peer_id)['upload_url']
        else:
            url = api.docs.getMessagesUploadServer(type='audio_message',peer_id=331465308)['upload_url']
        file = requests.post(url, files={
                    'file': open(file, 'rb')
                }).json()['file']
        file = api.docs.save(file=file)
        return f"doc{file['audio_message']['owner_id']}_{file['audio_message']['id']}_{file['audio_message']['access_key']}"

    def is_message_allowed(id_):
        try:
            return api.messages.isMessagesFromGroupAllowed(user_id=id_,group_id=config.vk_info['groupid'])['is_allowed']
        except:
            return api.messages.isMessagesFromGroupAllowed(user_id=id_,group_id=config.vk_info['groupid'])['is_allowed']

    def get_conversation_members(peer_id):
        try:
            return api.messages.getConversationMembers(group_id=config.vk_info['groupid'],peer_id=peer_id)['items']
        except Exception as e:
            if(e.code == 917):
                return 917

    def check_name(name):
        return api.utils.resolveScreenName(screen_name=name)

    def kick_user(chat,name):
        api.messages.removeChatUser(chat_id=chat-2000000000,member_id=name)

    def del_message(message_ids,delete_for_all=1,group_id=config.vk_info['groupid']):
        return api.messages.delete(message_ids=message_ids,delete_for_all=1,group_id=config.vk_info['groupid'])

    def set_typing(peer_id,type_='typing',group_id=config.vk_info['groupid']):
        api.messages.setActivity(group_id=config.vk_info['groupid'],peer_id=peer_id,type=type_)

    def check_keyboard(inline):
        if(inline):
            return "true"
        else:
            return "false"

    def twitch_api_auth():
        Mysql = Methods.Mysql()
        now = datetime.datetime.now().timestamp()
        auth = Mysql.query("SELECT * FROM twitch_api_keys WHERE `not-after`>%s LIMIT 1", (now))
        if(auth == None):
            data = {
                'client_id': config.client_id,
                'client_secret': config.twitch_api,
                'grant_type': "client_credentials"
            }
            auth = requests.post(f"https://id.twitch.tv/oauth2/token", headers=headers, data=data).json()
            Mysql.query("DELETE FROM twitch_api_keys")
            Mysql.query("INSERT INTO twitch_api_keys (`key_`, `not-after`, `type`, `client_id`) VALUES (%s, %s, %s, %s)", (auth['access_token'], now+auth['expires_in'], auth['token_type'], client_id))

            headers.update({
                'Authorization': f"{auth['token_type'].title()} {auth['access_token']}",
                'Client-ID': config.client_id,
            })
        else:
            headers.update({
                'Authorization': f"{auth['type'].title()} {auth['key_']}",
                'Client-ID': auth['client_id'],
                })
        headers.update({'Content-Type': "application/json"})
        Mysql.close()
        return headers

    def check_stream():
        headers = Methods.twitch_api_auth()
        params = {'user_login': config.streamer_info['id'], 'first': 1}
        response = requests.get("https://api.twitch.tv/helix/streams", params=params, headers=headers).json()
        if(response['data'] == []):
            return "Сейчас трансляция не ведётся."
        else:
            response = response['data'][0]
            return f"Название: {response['title']}\n\
                Игра: {response['game_name']}\n\
                Зрителей: {response['viewer_count']}\n\
                https://twitch.tv/{response['user_login']}"