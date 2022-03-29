#!/usr/bin/python3
import requests, time, builtins, os
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError

builtins.dir_path = os.path.dirname(os.path.realpath(__file__))

import config
from vk_commands import Commands
import methods

builtins.Mysql = methods.Mysql()

###
def start():
    try:
        builtins.Vk = methods.Vk(config.vk_info['access_token'])
        builtins.scrname = Vk.getById(config.vk_info['groupid'])[0]['screen_name']
        Vk.getLongPollServer()
        try:
            with open(dir_path+"/vk_TS", 'r') as f:
                Vk.updateParams(ts=f.read())
        except FileNotFoundError:
            pass
        try:
            os.mkdir(config.tmp_dir)
        except FileExistsError:
            for root, dirs, files in os.walk(config.tmp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        print("INFO", f"{scrname} успешно запущен.")
        while True:
                response = Vk.getMessages()
                if('failed' in response):
                    if(response['failed'] == 1):
                        Vk.updateParams(ts=response['ts'])
                    elif(response['failed'] == 2):
                        Vk.getLongPollServer(update_ts=False)
                    else:
                        Vk.getLongPollServer()
                    continue
                if(response['ts'] != Vk.getTS()):
                    Vk.updateParams(ts=response['ts'])
                    with open(dir_path+"/vk_TS", 'w') as f:
                        f.write(Vk.getTS())
                    for res in response['updates']:
                        Commands(res)
    except KeyboardInterrupt:
        print("INFO", "Завершение...")
        for root, dirs, files in os.walk(config.tmp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        Mysql.close()
        exit()

print("INFO", "Запуск бота...")
try:
    start()
except(ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
    print("ERROR", "Запуск не удался. Повтор через 10 секунд.")
    time.sleep(10)
    start()

