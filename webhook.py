#!/usr/bin/python3
### Discord management script
### Author: https://vk.com/l27001
import requests, json
from config import twitch_api, secret
import methods

if(__name__ == "__main__"):
    import sys
    try:
        action = sys.argv[1]
    except IndexError:
        print('./webhook.py <add|delete|list>')
        exit()
    if(action not in ['add','delete','list']): 
        print('./webhook.py <add|delete|list>')
        exit() 
    if(action == 'delete'):
        try:
            id_ = sys.argv[2]
        except IndexError:
            print('./webhook.py delete <id>')
            exit()
        headers = methods.twitch_api_auth()
        res = requests.delete("https://api.twitch.tv/helix/eventsub/subscriptions?id="+id_, headers=headers)
        if(res.status_code == 204):
            print("Success!")
        elif(res.status_code == 404):
            print("Invalid ID provided")
        else:
            print("Unknown code recieved", res.status_code)
    elif(action == 'add'):
        try:
            name = sys.argv[2]
            callback = sys.argv[3]
        except IndexError:
            print('./webhook.py add <name> <https://callback.example>')
            exit()
        headers = methods.twitch_api_auth()
        id_ = requests.get("https://api.twitch.tv/helix/users?login="+name, headers=headers).json()['data'][0]['id']

        data = {
            "type": "stream.online",
            "version": "1",
            "condition": {
                "broadcaster_user_id": id_
            },
            "transport": {
                "method": "webhook",
                "callback": callback,
                "secret": secret
            }
        }
        data = json.dumps(data)
        data = requests.post("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers, data=data).json()
        total = data['total']
        data = data['data'][0]
        print(f"Success!\nCheck is webhook confrimed with 'webhook.py list'\nAnd don't forget to change streamer_info['id'] in config!\nID: {data['id']}\nStatus: {data['status']}\nBroadcaster-ID: {data['condition']['broadcaster_user_id']}\nTotal webhook: {total}")
    elif(action == 'list'):
        headers = methods.twitch_api_auth()
        list_ = requests.get("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers).json()
        print(f"Total webhook: {list_['total']}")
        for data in list_['data']:
            print("-"*10)
            print(f"ID: {data['id']}\nStatus: {data['status']}\nBroadcaster-ID: {data['condition']['broadcaster_user_id']}\nLink: {data['transport']['callback']}")
            print("-"*10)
