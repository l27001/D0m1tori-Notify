#!/usr/bin/python3
from config import twitch_api, client_id, secret, discord
from hmac import new as hmac
from hashlib import sha256
from methods import Methods
from flask import Flask, request, abort, render_template, url_for, redirect, flash
from webhook import twitch_api_auth
import subprocess, datetime, os, requests
dir_path = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__,
        template_folder="web/templates/",
        static_folder="web/static/")
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['JSON_SORT_KEYS'] = False

@app.errorhandler(403)
def err403(e):
    return (render_template('error.html', code=403,
        description="Доступ запрещён",
        full_description="У Вас нет прав доступа к этому объекту. \
        Файл недоступен для чтения, или сервер не может его прочитать."), 403)

@app.errorhandler(404)
def err404(e):
    return (render_template('error.html', code=404,
        description="Страница не найдена",
        full_description="Страница которую вы запросили не может быть найдена.\
        Возможна она была удалена или перемещена."), 404)

@app.errorhandler(405)
def err405(e):
    return (render_template('error.html', code=405,
        description="Method not allowed",
        full_description="That method is not allowed for the requested URL."), 405)

@app.errorhandler(500)
def err500(e):
    return (render_template('error.html', code=500,
        description="Ошибка сервера",
        full_description="Во время обработки вашего запроса произошла ошибка. \
        Попробуйте позже или свяжитесь с разработчиком."), 500)

@app.route("/notify", methods=['POST'])
def notify():
    id_ = request.headers.get('Twitch-Eventsub-Message-Id')
    message_type = request.headers.get('Twitch-Eventsub-Message-Type')
    sign = request.headers.get('Twitch-Eventsub-Message-Signature')
    sub_type = request.headers.get('Twitch-Eventsub-Subscription-Type')
    timestamp = request.headers.get('Twitch-Eventsub-Message-Timestamp')
    if(id_ == None or message_type == None or sign == None or sub_type == None or timestamp == None):
        return abort(404)
    data = request.get_json()
    hmac_message = f"{id_}{timestamp}{request.get_data().decode()}"
    signature = 'sha256=' + str(hmac(secret.encode(), hmac_message.encode(), sha256).hexdigest())
    if(signature != sign):
        return abort(403)
    time = datetime.datetime.now() - datetime.timedelta(hours=3) - datetime.datetime.strptime(timestamp.split('.')[0], "%Y-%m-%dT%H:%M:%S")
    if(time > datetime.timedelta(minutes=10)):
        return abort(403)
    if(message_type == "webhook_callback_verification"):
        return data['challenge'], 200
    check = Methods.mysql_query("SELECT id FROM notify_ids WHERE id=%s", (id_))
    if(check != None):
        return abort(200)
    Methods.mysql_query("INSERT INTO notify_ids (`id`) VALUES (%s)", (id_))
    if(data['subscription']['status'] != "enabled"):
        Methods.send(331465308, f"Warning! Action required.\nTwitch notify status is '{data['subscription']['status']}'")
        return abort(200)
    subprocess.Popen(f"python3 {dir_path}/send.py {data['event']['broadcaster_user_id']}", shell=True)
    return abort(202)

@app.route('/notify/oauth')
def oauth():
    try:
        error = request.args.get('error').strip()
        description = request.args.get('error_description').strip()
        if(error):
            return {"status":"fail", "error":error, "description":description}, 400
    except AttributeError: pass
    try:
        code = request.args.get('code').strip()
        guild = request.args.get('guild_id').strip()
    except AttributeError: return abort(503)
    if(guild == '' or code == ''):
        return abort(503)
    check = Methods.mysql_query("SELECT id FROM webhooks WHERE guild = %s", (guild))
    if(check is not None):
        return {'status':'fail', 'description':'Для этого сервера уже добавлен вебхук', "check_webhook": "https://"+request.host+url_for("oauth_check", id_=guild)}, 400
    data = {
        'client_id': discord['client_id'],
        'client_secret': discord['client_secret'],
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': request.base_url.replace('http://', 'https://')
    }
    r = requests.post("https://discord.com/api/oauth2/token", data=data)
    if(r.status_code != 200):
        return abort(400)
    r = r.json()
    Methods.mysql_query("INSERT INTO webhooks (`link`, `guild`) VALUES (%s, %s)", (r['webhook']['url'], guild))
    return {'status':"ok"}, 202

@app.route('/notify/oauth/check_<int:id_>')
def oauth_check(id_):
    if(id_ <= 0): return abort(400)
    webhook = Methods.mysql_query("SELECT id,link FROM webhooks WHERE guild = %s", (id_))
    if(webhook is None): return {"status":"fail", "description":"Сервер с таким ID не найден в БД"}, 400
    r = requests.get(webhook['link'])
    r = r.json()
    if('code' in r):
        if(r['code'] == 10015):
            Methods.mysql_query("DELETE FROM webhooks WHERE id = %s", (webhook['id']))
            return {"status":"ok", "description":"Интеграция была удалёна с сервера. Запись удалена из БД"}
        elif(r['code'] == 50027):
            Methods.mysql_query("DELETE FROM webhooks WHERE id = %s", (webhook['id']))
            return {"status":"ok", "description":"Вебхук был удалён с сервера. Запись удалена из БД"}
        else: return {"status":"warning", "description":f"Получен неизвестный код {r['code']}. Никаких действий не выполнено, обратитесь к разработчику", "response":r}
    else:
        r['token'] = None
        return {"status":"ok", "description":"Похоже, что все в порядке.", "response":r}

# @app.route('/admin')
# def admin():
#     return render_template('admin.html')

if(__name__ == '__main__'):
    # app.run('127.0.0.254', port=5008, debug=True)
    from waitress import serve
    serve(app, host="127.0.0.254", port=5008)
