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
        self.from_user = response['object']['message']['from_id']
        self.from_chat = response['object']['message']['peer_id']
        self.inline = Vk.check_keyboard(response['object']['client_info']['inline_keyboard'])
        if(self.from_chat >= 2000000000):
            self.is_chat = True
            self.chat_sub = Mysql.query("SELECT * FROM vk_subscribe WHERE id = %s", (self.from_chat,))
            if(self.chat_sub == None):
                Mysql.query("INSERT INTO vk_subscribe (id) VALUES (%s)", (self.from_chat,))
                self.chat_sub = Mysql.query("SELECT * FROM vk_subscribe WHERE id = %s", (self.from_chat,))
        else:
            self.is_chat = False
            self.chat_sub = None
        self.user_sub = Mysql.query("SELECT * FROM vk_subscribe WHERE id = %s", (self.from_user,))
        if(self.user_sub == None):
            Mysql.query("INSERT INTO vk_subscribe (id) VALUES (%s)", (self.from_user,))
            self.user_sub = Mysql.query("SELECT * FROM vk_subscribe WHERE id = %s", (self.from_user,))
        if('payload' in response['object']['message']): # интенты подписки/отписки (только для пользователей)
            try:
                response['object']['message']['payload'] = json.loads(response['object']['message']['payload'])
                if('command' in response['object']['message']['payload'] and response['object']['message']['payload']['command'] == "internal_command"):
                    if(response['object']['message']['payload']['action']['type'] == "intent_unsubscribe"):
                        Mysql.query("UPDATE vk_subscribe SET subscribe = 0 WHERE id = %s", (self.from_user))
                        Vk.send(self.from_user, "Вы отписались от уведомлений о трансляциях.\nДля повторной подписки используйте команду '/рассылка'", keyboard=Vk.construct_keyboard(b1=Vk.make_button(type_="intent_subscribe",peer_id=self.from_user,intent="non_promo_newsletter",label="Подписаться"),inline=self.inline))
                    elif(response['object']['message']['payload']['action']['type'] == "intent_subscribe"):
                        Mysql.query("UPDATE vk_subscribe SET subscribe = 1 WHERE id = %s", (self.from_user))
                        Vk.send(self.from_user, "Вы подписались на уведомления о трансляциях.\nДля отписки используйте команду '/рассылка'", keyboard=Vk.construct_keyboard(b2=Vk.make_button(type_="intent_unsubscribe",peer_id=self.from_user,intent="non_promo_newsletter",label="Отписаться"),inline=self.inline))
                    return None
            except TypeError: pass # если пришел не json, то игнорируем
        self.text = response['object']['message']['text'].split()
        if(re.match(rf"\[(club|public){vk_info['groupid']}\|(@|\*){scrname}\]", self.text[0])):
            del(self.text[0])
        cmd = self.text[0].lower()
        del(self.text[0])
        if(cmds.get(cmd) == None):
            if(cmd[0] == '/' and self.is_chat == False):
                Vk.send(self.from_chat, "👎🏻 Не понял")
            return None
        try:
            cmds[cmd](self)
        except Exception as e:
            Vk.send(self.from_chat, "⚠ Произошла непредвиденная ошибка.\nОбратитесь к @l27001")
            raise e

    def info(self):
        """"""
        if(self.is_chat == True):
            if(self.chat_sub['subscribe'] == 1):
                rass_ch = f"Chat-ID: {self.from_chat}\nПодписка чата: Активна\n"
            else:
                rass_ch = f"Chat-ID: {self.from_chat}\nПодписка чата: Неактивна\n"
        else: rass_ch = ""
        if(self.user_sub['subscribe'] == 1):
            rass = "Активна"
        else: rass = "Неактивна"
        if(self.user_sub['dostup'] == 0): dostup = "Пользователь"
        elif(self.user_sub['dostup'] == 1): dostup = "Модератор"
        else: dostup = "Администратор"
        txt = f"ℹ️ Информация\nID: {self.from_user}\nДоступ: {dostup}\nПодписка: {rass}\n{rass_ch}"
        keyb = Vk.construct_keyboard(b1=Vk.make_button(color="secondary", label="/статус"), b2=Vk.make_button(color="primary", label="/рассылка"))
        Vk.send(self.from_chat, txt, keyboard=keyb, disable_mentions=1)

    def test(self):
        """"""
        Vk.send(self.from_chat, f"{scrname} Bot by @l27001", disable_mentions=1)

    def clrkeyb(self):
        """"""
        Vk.send(self.from_chat, "Clear keyboard", keyboard='{"buttons":[]}')

    def rass(self):
        """Подписка/Отписка от уведомлений о трансляциях"""
        if(self.is_chat == False):
            if(self.user_sub['subscribe'] == 0):
                Vk.send(self.from_chat,"Вы не подписаны", keyboard=Vk.construct_keyboard(b1=Vk.make_button(type_="intent_subscribe",peer_id=self.from_user,intent="non_promo_newsletter",label="Подписаться"),inline=self.inline))
            else:
                Vk.send(self.from_chat,"Вы подписаны", keyboard=Vk.construct_keyboard(b2=Vk.make_button(type_="intent_unsubscribe",peer_id=self.from_user,intent="non_promo_newsletter",label="Отписаться"),inline=self.inline))
        else:
            if(self.chat_sub['subscribe'] == 0):
                Mysql.query("UPDATE vk_subscribe SET subscribe = 1 WHERE id = %s", (self.from_chat,))
                Vk.send(self.from_chat,"Вы подписали беседу на рассылку обновлений расписания.\nДля рассылки лично вам напишите боту в ЛС.")
            else:
                Mysql.query("UPDATE vk_subscribe SET subscribe = 0 WHERE id = %s", (self.from_chat,))
                Vk.send(self.from_chat,"Вы отписали беседу от рассылки обновлений расписания.\nДля рассылки лично вам напишите боту в ЛС.")

    def help(self):
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
            cmd_list.append(f"{i} - {doc}")
        cmd_list = "\n".join(cmd_list)
        Vk.send(self.from_chat, cmd_list)

    def status(self):
        """Информация о трансляции"""
        Vk.send(self.from_chat, check_stream())

    def dsbot(self):
        """Уведомления о трансляциях на ваш сервер дискорд"""
        Vk.send(self.from_chat, "https://d0m1tori.ezdomain.ru/ds-notify/add")

cmds = {'/info':Commands.info, '/инфо':Commands.info, 
        '/test':Commands.test, '/тест':Commands.test, 
        '/рассылка':Commands.rass, '/подписаться':Commands.rass, '/отписаться':Commands.rass,
        '/help':Commands.help, '/помощь':Commands.help, 
        '/akey':Commands.clrkeyb,
        '/status':Commands.status, '/статус':Commands.status,
        '/дсбот':Commands.dsbot, '/dsbot':Commands.dsbot
}
