#!/usr/bin/python3
import telebot, builtins
import tg_methods as Methods

@bot.middleware_handler(update_types=['message'])
def modify_message(bot_instance, message):
    print(message)
    message.db_user = Methods.get_user(message.from_user.id)
    if(message.chat.type != 'private'):
        message.db_chat = Methods.get_chat(message.chat.id)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот D0m1tori Notify, я слежу за трансляциями и могу присылать уведомления о их начале, как по вашему запросу, так и при его обновлении на сайте.\nСписок команд можно получить введя команду <i>/помощь</i>\n\n<b><u>Telegram версия бота не является стабильной. Возможно вы захотите использовать версию ВКонтакте (vk.com/d0m1tori)</u></b>", parse_mode="HTML")

@bot.message_handler(commands=['help', 'помощь', 'команды', 'хелп'])
def send_help(message):
    bot.reply_to(message, "ℹ️ /info - Информация о пользователе\n/помощь - Список команд\n/рассылка - Подписаться/Отписаться от уведомлений о трансляциях\n/статус - Получить информацию о трансляции")

@bot.message_handler(commands=['subscribe', 'рассылка'], chat_types=['private'])
def subscribe(message):
    result = Methods.toggle_subscribe(message.from_user.id, message.db_user['subscribe'])
    if(result == 0):
        bot.reply_to(message, "✅ Вы успешно <u><b>отписались</b></u> от уведомлений о трансляциях", parse_mode="HTML")
    else:
        bot.reply_to(message, "✅ Вы успешно <u><b>подписались</b></u> на уведомления о трансляциях", parse_mode="HTML")

@bot.message_handler(commands=['subscribe', 'рассылка'], chat_types=['channel', 'group'])
def subscribe_chat(message):
    if(bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']):
        bot.reply_to(message, "⛔ Вы не администратор чата")
        return 0
    result = Methods.toggle_chat_subscribe(message.chat.id, message.db_chat['subscribe'])
    if(result == 0):
        bot.reply_to(message, "✅ Вы успешно <u><b>отписали</b></u> чат от уведомлений о трансляциях", parse_mode="HTML")
    else:
        bot.reply_to(message, "✅ Вы успешно <u><b>подписали</b></u> чат на уведомления о трансляциях", parse_mode="HTML")

@bot.message_handler(commands=['info'])
def info(message):
    if(message.db_user['subscribe'] == 0):
        sub = "Не активна"
    else:
        sub = "Активна"
    if(message.chat.type != 'private'):
        if(message.db_chat['subscribe'] == 0):
            chat_sub = "Не активна"
        else:
            chat_sub = "Активна"
        atxt = f"\nID Беседы: {message.db_chat['id']}\nПодписка беседы: {chat_sub}"
    else:
        atxt = ''
    bot.reply_to(message, f"ℹ️ Информация\n Имя: {message.from_user.first_name}\nФамилия: {message.from_user.last_name}\nTGID: {message.from_user.id}\nDostup: {message.db_user['dostup']}\nПодписка пользователя: {sub}{atxt}")

@bot.message_handler(commands=['статус', 'status'])
def status(message):
    bot.reply_to(message, Methods.check_stream(), allow_sending_without_reply=True)

@bot.message_handler(func=lambda message: True, chat_types=['private'])
def no_command(message):
    bot.reply_to(message, "👎🏻 Не понял.", allow_sending_without_reply=True)

# Methods.log("TG_INFO", "TG Bot запущен [BETA]")
bot.infinity_polling()
