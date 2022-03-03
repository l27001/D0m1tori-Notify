#!/usr/bin/python3
import requests, time, argparse, builtins, os, vk #, multiprocessing
from datetime import datetime
from OpenSSL.SSL import Error as VeryError
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError

parser = argparse.ArgumentParser()
parser.add_argument('-d','--debug', action='store_true', help="enable debug mode")
args = parser.parse_args()
builtins.DEBUG = args.debug
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
        #procs = []
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
            Methods.log("WARN", "Временная папка уже существует!")
            for root, dirs, files in os.walk(tmp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        finally:
            builtins.tmp_dir = tmp_dir
        Methods.log("INFO",f"{scrname['name']} успешно запущен.")
        while True:
            try:
        #        for i in range(len(procs)-1, -1, -1):
        #            code = procs[i].exitcode
        #            if(code == None):
        #                pass
        #            elif(code == 0):
        #                procs[i].join()
        #                del(procs[i])
        #            else:
        #                procs[i].join()
        #                del(procs[i])
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
                    if(DEBUG == True):
                        Methods.log("Debug", f"Получен некорректный ответ. Код: {response['failed']}.")
                    continue
                if(response['ts'] != ts):
                    ts = response['ts']
                    with open(dir_path+"/TS", 'w') as f:
                        f.write(ts)
                    for res in response['updates']:
         #               t = multiprocessing.Process(target=Commands, name=f"{ts}", args=(res,))
         #               t.start()
         #               procs.append(t)
                        Commands(res)
            except(VeryError, ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
                Methods.log("WARN","Сервер не ответил. Жду 3 секунды перед повтором.")
                time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        Methods.log("INFO", "Завершение...")
        for root, dirs, files in os.walk(tmp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        count = 0
        while len(procs) != 0:
            if(count > 10):
                Methods.log("WARN", f"Не могу завершить подпроцесс(ы). {procs}")
            for i in range(len(procs)-1, -1, -1):
                code = procs[i].exitcode
                if(code == None):
                    pass
                elif(code == 0):
                    procs[i].join()
                    del(procs[i])
                else:
                    procs[i].join()
                    del(procs[i])
            count += 1
        os.rmdir(tmp_dir)
        Mysql.close()
        exit()

Methods.log("INFO", "Запуск бота...")
try:
    start()
except(ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
    Methods.log("ERROR", "Запуск не удался. Повтор через 10 секунд.")
    time.sleep(10)
    start()

