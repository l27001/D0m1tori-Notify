#!/usr/bin/python3
import requests, time, builtins, os, vk #, multiprocessing
from datetime import datetime
from OpenSSL.SSL import Error as VeryError
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError

builtins.dir_path = os.path.dirname(os.path.realpath(__file__))

from config import tmp_dir, vk_info
from commands import Commands
from methods import Methods

builtins.Mysql = Methods.Mysql()
session = vk.Session(access_token=vk_info['access_token'])
builtins.api = vk.API(session, v='5.124', lang='ru')

###
def start():
    try:
        scrname = api.groups.getById(group_id=vk_info['groupid'])[0]
        builtins.scrname = scrname['screen_name']
        lp = api.groups.getLongPollServer(group_id=vk_info['groupid'])
        server = lp['server']
        key = lp['key']
        try:
            with open(dir_path+"/TS", 'r') as f:
                ts = f.read()
        except FileNotFoundError:
            ts = lp['ts']
        try:
            os.mkdir(tmp_dir)
        except FileExistsError:
            print("WARN", "Временная папка уже существует!")
            for root, dirs, files in os.walk(tmp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        finally:
            builtins.tmp_dir = tmp_dir
        print("INFO",f"{scrname['name']} успешно запущен.")
        while True:
            try:
                response = requests.get(server+"?act=a_check&key="+key+"&ts="+ts+"&wait=60",timeout=61).json()
                if('failed' in response):
                    if(response['failed'] == 1):
                        ts = response['ts']
                    elif(response['failed'] == 2):
                        lp = api.groups.getLongPollServer(group_id=vk_info['groupid'])
                        server = lp['server']
                        key = lp['key']
                    else:
                        lp = api.groups.getLongPollServer(group_id=vk_info['groupid'])
                        server = lp['server']
                        key = lp['key']
                        ts = lp['ts']
                    continue
                if(response['ts'] != ts):
                    ts = response['ts']
                    with open(dir_path+"/TS", 'w') as f:
                        f.write(ts)
                    for res in response['updates']:
                        Commands(res)
            except(VeryError, ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
                print("WARN","Сервер не ответил. Жду 3 секунды перед повтором.")
                time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        print("INFO", "Завершение...")
        for root, dirs, files in os.walk(tmp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(tmp_dir)
        Mysql.close()
        exit()

print("INFO", "Запуск бота...")
try:
    start()
except(ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
    print("ERROR", "Запуск не удался. Повтор через 10 секунд.")
    time.sleep(10)
    start()

