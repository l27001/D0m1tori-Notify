#!/usr/bin/python3
import requests, json
from config import twitch_api, callback, secret
from methods import Methods

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
        headers = Methods.twitch_api_auth()
        print(requests.delete("https://api.twitch.tv/helix/eventsub/subscriptions?id="+id_, headers=headers))
    elif(action == 'add'):
        try:
            name = sys.argv[2]
            callback = sys.argv[3]
        except IndexError:
            print('./webhook.py add <name> <https://callback.example>')
            exit()
        headers = Methods.twitch_api_auth()
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
        print(data)
    elif(action == 'list'):
        headers = Methods.twitch_api_auth()
        print(requests.get("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers).json())
