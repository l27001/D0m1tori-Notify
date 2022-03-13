import builtins, os, telebot
import config
from methods import Methods
builtins.Mysql = Methods.Mysql()
builtins.dir_path = os.path.dirname(os.path.realpath(__file__))
telebot.apihelper.ENABLE_MIDDLEWARE = True
builtins.bot = telebot.TeleBot(config.tg_info['access_token'])

def get_user(id_):
    user = Mysql.query("SELECT * FROM tg_users WHERE tgid = %s", id_)
    if(user is not None):
        return user
    else:
        Mysql.query("INSERT INTO tg_users (`tgid`) VALUES (%s)", id_)
        return Mysql.query("SELECT * FROM tg_users WHERE tgid = %s", id_)

def get_chat(id_):
    chat = Mysql.query("SELECT * FROM tg_chats WHERE id = %s", id_)
    if(chat is not None):
        return chat
    else:
        Mysql.query("INSERT INTO tg_chats (`id`) VALUES (%s)", id_)
        return Mysql.query("SELECT * FROM tg_chats WHERE id = %s", id_)

def toggle_subscribe(id_, sub):
    if(sub == 0):
        Mysql.query("UPDATE tg_users SET subscribe = 1 WHERE tgid = %s", id_)
        return 1
    else:
        Mysql.query("UPDATE tg_users SET subscribe = 0 WHERE tgid = %s", id_)
        return 0

def toggle_chat_subscribe(id_, sub):
    if(sub == 0):
        Mysql.query("UPDATE tg_chats SET subscribe = 1 WHERE id = %s", id_)
        return 1
    else:
        Mysql.query("UPDATE tg_chats SET subscribe = 0 WHERE id = %s", id_)
        return 0

def setting_get(*args, **kwargs):
    return Methods.setting_get(*args, **kwargs)

def setting_set(*args, **kwargs):
    return Methods.setting_set(*args, **kwargs)

def setting_del(*args, **kwargs):
    return Methods.setting_del(*args, **kwargs)

def log(prefix, text):
    Methods.log(prefix, text)

def check_stream(*args, **kwargs):
    return Methods.check_stream(*args, **kwargs)

def send_notify(txt, link=""):
    users = Mysql.query("SELECT tgid FROM tg_users WHERE subscribe = 1", fetch="all")
    for user in users:
        try:
            bot.send_message(user['tgid'], txt+"\n"+link, "HTML", disable_notification=False)
        except Exception as e:
            log("TG_ERR", str(e)+" | User: "+str(user['tgid']))
    chats = Mysql.query("SELECT id FROM tg_chats WHERE subscribe = 1", fetch="all")
    for chat in chats:
        try:
            bot.send_message(chat['id'], txt+"\n"+link, "HTML", disable_notification=False)
        except Exception as e:
            log("TG_ERR", str(e)+" | Chat: "+str(chat['id']))
