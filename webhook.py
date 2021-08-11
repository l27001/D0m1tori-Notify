#!/usr/bin/python3
import requests, json, datetime
from config import twitch_api, callback, client_id, secret
from methods import Methods

def twitch_api_auth():
    now = datetime.datetime.now().timestamp()
    auth = Mysql.query("SELECT * FROM twitch_api_keys WHERE `not-after`>%s LIMIT 1", (now))
    headers = {
        'User-Agent': "D0m1toriBot"
    }
    if(auth == None):
        data = {
            'client_id': client_id,
            'client_secret': twitch_api,
            'grant_type': "client_credentials"
        }
        auth = requests.post(f"https://id.twitch.tv/oauth2/token", headers=headers, data=data).json()
        Mysql.query("DELETE FROM twitch_api_keys")
        Mysql.query("INSERT INTO twitch_api_keys (`key_`, `not-after`, `type`, `client_id`) VALUES (%s, %s, %s, %s)", (auth['access_token'], now+auth['expires_in'], auth['token_type'], client_id))

        headers.update({
            'Authorization': f"{auth['token_type'].title()} {auth['access_token']}",
            'Client-ID': client_id,
        })
    else:
        headers.update({
            'Authorization': f"{auth['type'].title()} {auth['key_']}",
            'Client-ID': auth['client_id'],
            })
    headers.update({'Content-Type': "application/json"})
    return headers
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
    Mysql = Methods.Mysql()
    if(action == 'delete'):
        try:
            id_ = sys.argv[2]
        except IndexError:
            print('./webhook.py delete <id>')
            exit()
        headers = twitch_api_auth()
        print(requests.delete("https://api.twitch.tv/helix/eventsub/subscriptions?id="+id_, headers=headers))
    elif(action == 'add'):
        try:
            name = sys.argv[2]
            callback = sys.argv[3]
        except IndexError:
            print('./webhook.py add <name> <https://callback.example>')
            exit()
        headers = twitch_api_auth()
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
        headers = twitch_api_auth()
        print(requests.get("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers).json())
    Mysql.close()
