import re, json
from config import vk_info
from methods import check_stream

class Commands:

    def __init__(self, response):
        if(response['type'] not in ['message_new', 'group_leave']):
            return None
        if(response['type'] == 'group_leave'):
            if(Vk.is_message_allowed(response['object']['user_id']) == 1):
                Vk.send(response['object']['user_id'], "Очень жаль, что ты покидаешь нас :(")
            return None
        obj = response['object']['message']
        client_info = response['object']['client_info']
        if 'reply_message' in obj:
            replid = obj['reply_message']['from_id']
        else:
            replid = ''
        from_id = obj['from_id']
        chat_id = obj['peer_id']
        text = obj['text']
        if(from_id < 1 or text == ''):
            return None
        userinfo = Mysql.query("SELECT * FROM users WHERE vkid='"+str(from_id)+"' LIMIT 1")
        if(userinfo == None):
            Mysql.query(f"INSERT INTO users (`vkid`) VALUES ('{from_id}')")
            userinfo = Mysql.query(f"SELECT * FROM users WHERE vkid='{from_id}' LIMIT 1")
        tlog = text.replace("\n",r" \n ")
        if('payload' in obj):
            try:
                obj['payload'] = json.loads(obj['payload'])
                if('command' in obj['payload'] and obj['payload']['command'] == "internal_command"):
                    inline = Vk.check_keyboard(client_info['inline_keyboard'])
                    if(obj['payload']['action']['type'] == "intent_unsubscribe"):
                        Mysql.query(f"UPDATE users SET notify='0' WHERE vkid='{from_id}'")
                        Vk.send(from_id, "Вы отписались от уведомлений о трансляциях.\nДля повторной подписки используйте команду '/рассылка'", keyboard=Vk.construct_keyboard(b1=Vk.make_button(type="intent_subscribe",peer_id=from_id,intent="non_promo_newsletter",label="Подписаться"),inline=inline))
                    elif(obj['payload']['action']['type'] == "intent_subscribe"):
                        Mysql.query(f"UPDATE users SET notify='1' WHERE vkid='{from_id}'")
                        Vk.send(from_id, "Вы подписались на уведомления о трансляциях.\nДля отписки используйте команду '/рассылка'", keyboard=Vk.construct_keyboard(b2=Vk.make_button(type="intent_unsubscribe",peer_id=from_id,intent="non_promo_newsletter",label="Отписаться"),inline=inline))
                    return None
            except TypeError: pass
            userinfo.update({'payload':obj['payload']})
        text = text.split(' ')
        if(re.match(rf"\[(club|public){vk_info['groupid']}\|(@|\*){scrname}\]", text[0])):
            text.pop(0)
        if(text[0][0] != '/'):
            return None
        elif(chat_id > 2000000000):
            chatinfo = Mysql.query(f"SELECT * FROM chats WHERE id = '{chat_id}' LIMIT 1")
            if(chatinfo == None):
                Mysql.query(f"INSERT INTO chats (`id`) VALUES ({chat_id})")
                chatinfo = Mysql.query(f"SELECT * FROM chats WHERE id = '{chat_id}' LIMIT 1")
            userinfo.update({'chatinfo':chatinfo})
        text[0] = text[0].lower()
        text[0] = text[0].replace('/','')
        userinfo.update({'replid':replid,'chat_id':chat_id, 'from_id':from_id, 'attachments':obj['attachments'], 'inline':client_info['inline_keyboard']})
        if(cmds.get(text[0]) == None):
            # if(chat_id < 2000000000):
                # Vk.send(chat_id, "👎🏻 Не понял.")
            return None
        else:
            try:
                cmds[text[0]](userinfo, text[1:])
            except Exception as e:
                Vk.send(chat_id, "⚠ Произошла непредвиденная ошибка.\nОбратитесь к @l27001")
                raise e

    def info(userinfo, text):
        """"""
        if(len(text) < 1):
            text.insert(0, str(userinfo['from_id']))
        t = re.findall(r'\[.*\|', text[0])
        try:
            t = t[0].replace("[", "").replace("|", "")
        except IndexError:
            t = text[0]
        if('payload' in userinfo):
            t = userinfo['payload']
        try:
            uinfo = Vk.users_get(t)
        except Exception as e:
            if(e.code == 113):
                Vk.send(userinfo['chat_id'], "⚠ Invalid user_id")
                return 0
        name = f"[id{uinfo[0]['id']}|{uinfo[0]['last_name']} {uinfo[0]['first_name']}]"
        uinfo = Mysql.query(f"SELECT * FROM users WHERE vkid='{uinfo[0]['id']}' LIMIT 1")
        if(uinfo == None):
            Vk.send(userinfo['chat_id'], "⚠ Пользователь не найден в БД")
            return 0
        if(uinfo['notify'] == 0):
            notify = 'Рассылка: Не подписан'
        else:
            notify = 'Рассылка: Подписан'
        if(userinfo['chat_id'] != userinfo['from_id']):
            ch = f"\nChat-ID: {userinfo['chat_id']}"
        else:
            ch = ''
        keyb = Vk.construct_keyboard(b2=Vk.make_button(color="primary", label="/рассылка"))
        Vk.send(userinfo['chat_id'], "Имя: "+name+"\nVKID: "+str(uinfo['vkid'])+"\nDostup: "+str(uinfo['dostup'])+"\n"+notify+ch, keyboard=keyb, disable_mentions=1)

    def test(userinfo, text):
        """"""
        Vk.send(userinfo['chat_id'], f"{scrname} Bot by @l27001", disable_mentions=1)

    def clrkeyb(userinfo, text):
        """"""
        Vk.send(userinfo['chat_id'], "Clear keyboard", keyboard='{"buttons":[]}')

    def rass(userinfo, text):
        """Подписка/Отписка от уведомлений о трансляциях"""
        if(userinfo['chat_id'] == userinfo['from_id']):
            if(userinfo['notify'] == 0):
                Vk.send(userinfo['chat_id'],"Вы не подписаны", keyboard=Vk.construct_keyboard(b1=Vk.make_button(type="intent_subscribe",peer_id=userinfo['from_id'],intent="non_promo_newsletter",label="Подписаться"),inline=Vk.check_keyboard(userinfo['inline'])))
            else:
                Vk.send(userinfo['chat_id'],"Вы подписаны", keyboard=Vk.construct_keyboard(b2=Vk.make_button(type="intent_unsubscribe",peer_id=userinfo['from_id'],intent="non_promo_newsletter",label="Отписаться"),inline=Vk.check_keyboard(userinfo['inline'])))
        else:
            count = Mysql.query(f"SELECT COUNT(*) FROM `chats` WHERE id = {userinfo['chat_id']} AND `notify`=1")['COUNT(*)']
            if(count != 1):
                Mysql.query(f"UPDATE `chats` SET `notify`=1 WHERE `id`='{userinfo['chat_id']}'")
                Vk.send(userinfo['chat_id'],"Вы подписали беседу на рассылку обновлений расписания.\nДля рассылки лично вам напишите боту в ЛС.")
            else:
                Mysql.query(f"UPDATE `chats` SET `notify`=0 WHERE `id`='{userinfo['chat_id']}'")
                Vk.send(userinfo['chat_id'],"Вы отписали беседу от рассылки обновлений расписания.\nДля рассылки лично вам напишите боту в ЛС.")

    def help(userinfo, text):
        """Помощь"""
        cmd_list = []
        pred = None
        for i,n in cmds.items():
            if(n == pred):
                continue
            pred = n
            if(n.__doc__ == None or n.__doc__ == ''):
                continue
            else:
                doc = n.__doc__
            cmd_list.append(f"/{i} - {doc}")
        cmd_list = "\n".join(cmd_list)
        Vk.send(userinfo['chat_id'], cmd_list)

    def status(userinfo, text):
        """Информация о трансляции"""
        Vk.send(userinfo['chat_id'], check_stream())

    def dsbot(userinfo, text):
        """Уведомления о трансляциях на ваш сервер дискорд"""
        Vk.send(userinfo['chat_id'], "https://test.ezdomain.ru/ds-notify/add")

cmds = {'info':Commands.info, 'инфо':Commands.info, 
'test':Commands.test, 'тест':Commands.test, 
'рассылка':Commands.rass, 'подписаться':Commands.rass, 'отписаться':Commands.rass,
'help':Commands.help, 'помощь':Commands.help, 
'akey':Commands.clrkeyb,
'status':Commands.status, 'статус':Commands.status,
'дсбот':Commands.dsbot, 'dsbot':Commands.dsbot
}
