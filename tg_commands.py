from methods import check_stream

class Commands:

    def __init__(self, data):
        if('my_chat_member' in data):
            return None
        elif('message' in data):
            data = data['message']
            if('text' not in data): # исключение/добавление участника приходит с элементом message
                return None         # но без text в нём. Игнорируем такие события
            self.from_user = data['from']['id']
            self.from_chat = data['chat']['id']
            if(self.from_chat < 0): self.is_chat = True
            else: self.is_chat = False
            self.text = data['text'].split()
            self.msg_id = data['message_id']
        if(self.is_chat):
            self.chat_sub = Mysql.query("SELECT * FROM tg_subscribe WHERE id = %s", (self.from_chat,))
            if(self.chat_sub == None):
                Mysql.query("INSERT INTO tg_subscribe (id) VALUES (%s)", (self.from_chat,))
                self.chat_sub = Mysql.query("SELECT * FROM tg_subscribe WHERE id = %s", (self.from_chat,))
            self.text[0] = self.text[0].split("@")
            if(len(self.text[0]) > 1):
                if(self.text[0][1] != Tg.username): # Фильтруем команды по тегу бота
                    return None                     # Пример: /status@first_bot и /status@second_bot
            self.text[0] = self.text[0][0] # убираем тег из команды
        else: self.chat_sub = None
        self.user_sub = Mysql.query("SELECT * FROM tg_subscribe WHERE id = %s", (self.from_user,))
        if(self.user_sub == None):
            Mysql.query("INSERT INTO tg_subscribe (id) VALUES (%s)", (self.from_user,))
            self.user_sub = Mysql.query("SELECT * FROM tg_subscribe WHERE id = %s", (self.from_user,))
        cmd = self.text[0].lower()
        del(self.text[0])
        if(cmds.get(cmd) == None):
            if(self.is_chat == False):
                Tg.sendMessage(self.from_chat, "👎🏻 Не понял", reply_to_message_id=self.msg_id)
            return None
        try:
            cmds[cmd](self)
        except Exception as e:
            Tg.sendMessage(self.from_chat, "⚠ Произошла непредвиденная ошибка.\nОбратитесь к @l270011", reply_to_message_id=self.msg_id)
            print(e)

    def start(self):
        Tg.sendMessage(self.from_chat, "Привет! Я бот D0m1tori Notify, я слежу за трансляциями и могу присылать уведомления о их начале, как по вашему запросу, так и при его обновлении на сайте.\nСписок команд можно получить введя команду <i>/помощь</i>\n\n<b><u>Telegram версия бота не является стабильной. Возможно вы захотите использовать версию ВКонтакте (vk.com/d0m1tori)</u></b>", parse_mode="HTML", reply_to_message_id=self.msg_id)

    def test(self):
        Tg.sendMessage(self.from_chat, "TG bot by @l270011", reply_to_message_id=self.msg_id)

    def info(self):
        if(self.is_chat):
            if(self.chat_sub['subscribe'] == 1):
                rassb = f"Chat-ID: {self.from_chat}\nПодписка чата: *Активна*\n"
            else:
                rassb = f"Chat-ID: {self.from_chat}\nПодписка чата: *Неактивна*\n"
        else: rassb = ""
        if(self.user_sub['subscribe'] == 1):
            rass = "Активна"
        else:
            rass = "Неактивна"
        txt = f"ℹ️ Информация\nID: {self.from_user}\nПодписка: *{rass}*\n{rassb}"
        Tg.sendMessage(self.from_chat, txt, reply_to_message_id=self.msg_id)

    def subscribe(self):
        if(self.is_chat):
            if(self.chat_sub['subscribe'] == 1):
                Mysql.query("UPDATE tg_subscribe SET subscribe=0 WHERE id = %s", (self.from_chat,))
                txt = "✅ Вы успешно *отписали беседу* от уведомлений о трансляциях"
            else:
                Mysql.query("UPDATE tg_subscribe SET subscribe=1 WHERE id = %s", (self.from_chat,))
                txt = "✅ Вы успешно *подписали беседу* на уведомления о трансляциях"
        else:
            if(self.user_sub['subscribe'] == 1):
                Mysql.query("UPDATE tg_subscribe SET subscribe=0 WHERE id = %s", (self.from_user,))
                txt = "✅ Вы успешно *отписались* от уведомлений о трансляциях"
            else:
                Mysql.query("UPDATE tg_subscribe SET subscribe=1 WHERE id = %s", (self.from_user,))
                txt = "✅ Вы успешно *подписались* на уведомления о трансляциях"
        Tg.sendMessage(self.from_chat, txt, reply_to_message_id=self.msg_id)

    def status(self):
        Tg.sendMessage(self.from_chat, check_stream(), reply_to_message_id=self.msg_id)

cmds = {'/start':Commands.start,
        '/test':Commands.test,
        '/info':Commands.info,
        '/subscribe':Commands.subscribe,'/unsubscribe':Commands.subscribe,
        '/status':Commands.status}
