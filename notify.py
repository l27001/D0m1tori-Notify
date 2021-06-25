#!/usr/bin/python3
from config import twitch_api, client_id, secret
from hmac import new as hmac
from hashlib import sha256
from methods import Methods
from flask import Flask, request
from webhook import twitch_api_auth
import subprocess, datetime, os
dir_path = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

@app.route("/notify", methods=['POST'])
def notify():
    id_ = request.headers.get('Twitch-Eventsub-Message-Id')
    message_type = request.headers.get('Twitch-Eventsub-Message-Type')
    sign = request.headers.get('Twitch-Eventsub-Message-Signature')
    sub_type = request.headers.get('Twitch-Eventsub-Subscription-Type')
    timestamp = request.headers.get('Twitch-Eventsub-Message-Timestamp')
    if(id_ == None or message_type == None or sign == None or sub_type == None or timestamp == None):
        return '', 404
    data = request.get_json()
    hmac_message = f"{id_}{timestamp}{request.get_data().decode()}"
    signature = 'sha256=' + str(hmac(secret.encode(), hmac_message.encode(), sha256).hexdigest())
    if(signature != sign):
        return '', 403
    time = datetime.datetime.now() - datetime.timedelta(hours=3) - datetime.datetime.strptime(timestamp.split('.')[0], "%Y-%m-%dT%H:%M:%S")
    if(time > datetime.timedelta(minutes=10)):
        return '', 403
    if(message_type == "webhook_callback_verification"):
        return data['challenge'], 200
    check = Methods.mysql_query("SELECT id FROM notify_ids WHERE id=%s", (id_))
    if(check != None):
        return '', 200
    Methods.mysql_query("INSERT INTO notify_ids (`id`) VALUES (%s)", (id_))
    if(data['subscription']['status'] != "enabled"):
        Methods.send(331465308, f"Warning! Action required.\nTwitch notify status is '{data['subscription']['status']}'")
        return '', 200
    subprocess.Popen(f"python3 {dir_path}/send.py {data['event']['broadcaster_user_id']}", shell=True)
    return '', 202

if(__name__ == '__main__'):
    # app.run('127.0.0.254', port=5008, debug=True)
    from waitress import serve
    serve(app, host="127.0.0.254", port=5008)
