#!/usr/bin/python3
import requests, time, builtins, os, sys
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
import config
import methods
from tg_commands import Commands

builtins.dir_path = os.path.dirname(os.path.realpath(__file__))
builtins.Mysql = methods.Mysql()

try:
    print("INFO", "Запуск бота...")
    builtins.Tg = methods.Tg()
    if(os.path.isdir(config.tmp_dir) != True):
        os.mkdir(config.tmp_dir)
    if(os.path.isfile(dir_path+"/tg_TS") == True):
        with open(dir_path+"/tg_TS") as f:
            Tg.setOffset(f.read())
    while True:
        offset = Tg.getOffset()
        data = Tg.getUpdates(offset=offset)
        if(offset != Tg.getOffset()):
            with open(dir_path+"/tg_TS", "w") as f:
                f.write(str(Tg.getOffset()))
        for n in data['result']:
            Commands(n)

except KeyboardInterrupt:
    pass
except(ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
    print("ERROR", "Запуск не удался.")
    sys.exit(1)
finally:
    print("INFO", "Завершение...")
