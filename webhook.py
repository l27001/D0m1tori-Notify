#!/usr/bin/python3
import requests, json, datetime
from config import twitch_api, callback, client_id, secret
from methods import Methods

def twitch_api_auth():
    now = datetime.datetime.now().timestamp()
    auth = Methods.mysql_query("SELECT * FROM twitch_api_keys WHERE `not-after`>%s LIMIT 1", (now))
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
        Methods.mysql_query("INSERT INTO twitch_api_keys (`key_`, `not-after`, `type`, `client_id`) VALUES (%s, %s, %s, %s)", (auth['access_token'], now+auth['expires_in'], auth['token_type'], client_id))

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
    headers = twitch_api_auth()
    id_ = requests.get("https://api.twitch.tv/helix/users?login=d0m1tori", headers=headers).json()['data'][0]['id']

    data = {
        "type": "stream.online",
        "version": "1",
        "condition": {
            "broadcaster_user_id": id_
        },
        "transport": {
            "method": "webhook",
            "callback": "https://d0m1tori.ezdn.ru/notify",
            "secret": secret
        }
    }

    # print(requests.delete("https://api.twitch.tv/helix/eventsub/subscriptions?id=e1531cfc-dd96-4004-98e6-d0bbbcde60b5", headers=headers))

    # data = json.dumps(data)
    # data = requests.post("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers, data=data).json()
    # print(data)

    print(requests.get("https://api.twitch.tv/helix/eventsub/subscriptions", headers=headers).json())