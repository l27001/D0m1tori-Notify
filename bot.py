#!/usr/bin/python3
import requests, time, multiprocessing, argparse, builtins, os
from datetime import datetime
from random import randint
from OpenSSL.SSL import Error as VeryError
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError

parser = argparse.ArgumentParser()
parser.add_argument('-d','--debug', action='store_true', help="enable debug mode")
args = parser.parse_args()
builtins.DEBUG = args.debug
builtins.acmds = 0
builtins.aerrs = 0
builtins.timestart = datetime.now()

from config import groupid, tmp_dir
from other import dir_path, api
from commands import Commands
from methods import Methods

###
def start():
    try:
        procs = []
        scrname = api.groups.getById(group_id=groupid)[0]
        builtins.scrname = scrname['screen_name']
        lp = api.groups.getLongPollServer(group_id=groupid)
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
                for i in range(len(procs)-1, -1, -1):
                    code = procs[i].exitcode
                    if(code == None):
                        pass
                    elif(code == 0):
                        procs[i].join()
                        del(procs[i])
                        builtins.acmds += 1
                    else:
                        procs[i].join()
                        del(procs[i])
                        builtins.acmds += 1
                        builtins.aerrs += 1
                response = requests.get(server+"?act=a_check&key="+key+"&ts="+ts+"&wait=20",timeout=22).json()
                if 'failed' in response:
                    lp = api.groups.getLongPollServer(group_id=groupid)
                    server = lp['server']
                    key = lp['key']
                    if(DEBUG == True):
                        Methods.log("Debug","Получен некорректный ответ. Ключ обновлен.")
                    continue
                if(response['ts'] != ts):
                    ts = response['ts']
                    with open(dir_path+"/TS", 'w') as f:
                        f.write(ts)
                    for res in response['updates']:
                        t = multiprocessing.Process(target=Commands, name=f"{ts}", args=(res,))
                        t.start()
                        procs.append(t)
            except(VeryError, ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
                Methods.log("WARN","Сервер не ответил. Жду 3 секунды перед повтором.")
                time.sleep(3)
    except KeyboardInterrupt:
        Methods.log("INFO","Завершение...")
        for root, dirs, files in os.walk(tmp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(tmp_dir)
        exit()

Methods.log("INFO",f"Запуск бота...")
try:
    start()
except(ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
    Methods.log("ERROR","Запуск не удался. Повтор через 10 секунд.")
    time.sleep(10)
    start()