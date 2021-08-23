#!/usr/bin/python3
from config import twitch_api, client_id, secret, discord, vk_app
from hmac import new as hmac
from hashlib import sha256
from methods import Methods
from flask import Flask, request, abort, render_template, url_for, redirect, flash, g, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from webhook import twitch_api_auth
import subprocess, datetime, os, requests, hashlib
import send
dir_path = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__,
        template_folder="web/templates/",
        static_folder="web/assets/")
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['JSON_SORT_KEYS'] = False
app.config['CSRF_ENABLED'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SECRET_KEY'] = "ZXd1yoMX_8$nkDD+w^H!8qC+yt8N$YMQl-sIrMuQ0w-c3ciUsRqH52HCfVt3S^!f"

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'auth'

def subp(cmd, shell=False):
    if(shell):
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    else:
        proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    proc.wait()
    return proc.communicate()[0].decode()[:-1]

class User():
    def __init__(self, user):
        if(user == None or user['dostup'] < 2):
            self.is_authenticated = False
            self.is_active = False
            self.is_anonymous = False
            self.id = -1
        else:
            self.is_authenticated = True
            self.is_active = True
            self.is_anonymous = False
            self.id = user['vkid']
            self.dostup = user['dostup']
            self.info = user

    def get_id(self):
        return self.id

@lm.unauthorized_handler
def unauthorized():
    if(request.method == "GET"):
        return redirect(url_for('auth'))
    else:
        return {"status":"unauthorized", "description":"Необходимо авторизоваться"}

@app.before_request
def before_request():
    if(request.path.startswith('/assets/')):
        return None
    g.user = current_user
    if(g.user is not None and g.user.is_authenticated == True):
        if(Mysql.query("SELECT vkid FROM users WHERE vkid = %s AND dostup >= 2", (g.user.id)) is None):
            logout_user()
            return redirect(url_for('auth'))

@lm.user_loader
def load_user(user_id):
    return User(Mysql.query("SELECT * FROM users WHERE vkid=%s LIMIT 1", (user_id)))

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
    check = Mysql.query("SELECT id FROM notify_ids WHERE id=%s", (id_))
    if(check != None):
        return '', 204
    if(data['subscription']['status'] != "enabled"):
        Methods.send(331465308, f"Warning! Action required.\nTwitch notify status is '{data['subscription']['status']}'")
        return '', 204
    subprocess.Popen(f"python3 {dir_path}/send.py {data['event']['broadcaster_user_id']}", shell=True)
    Mysql.query("INSERT INTO notify_ids (`id`) VALUES (%s)", (id_))
    return '', 202

@app.route('/notify/oauth')
def oauth():
    try:
        error = request.args.get('error').strip()
        description = request.args.get('error_description').strip()
        if(error):
            return render_template('message.html', title="Информация", status="fail", msg=description), 400
    except AttributeError: pass
    try:
        code = request.args.get('code').strip()
        guild = request.args.get('guild_id').strip()
    except AttributeError: return abort(503)
    if(guild == '' or code == ''):
        return abort(503)
    check = Mysql.query("SELECT id FROM webhooks WHERE guild = %s", (guild))
    if(check is not None):
        return render_template('message.html', title="Информация", status="info", msg='Для этого сервера уже добавлен вебхук', buttons=[{'link':"https://"+request.host+url_for("oauth_check", id_=guild), 'text':'Проверить вебхук'}])
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
    Mysql.query("INSERT INTO webhooks (`link`, `guild`) VALUES (%s, %s)", (r['webhook']['url'], guild))
    return render_template('message.html', title="Информация", status="success", msg="Вебхук успешно добавлен"), 202

@app.route('/notify/oauth/check_<int:id_>')
def oauth_check(id_):
    if(id_ <= 0): return abort(400)
    webhook = Mysql.query("SELECT id,link FROM webhooks WHERE guild = %s", (id_))
    if(webhook is None): return render_template('message.html', title="Информация", status="fail", msg="Сервер с таким ID не найден в БД"), 400
    r = requests.get(webhook['link'])
    r = r.json()
    if('code' in r):
        if(r['code'] == 10015):
            Mysql.query("DELETE FROM webhooks WHERE id = %s", (webhook['id']))
            return render_template('message.html', title="Информация", status="info", msg="Интеграция была удалёна с сервера. Запись удалена из БД")
        elif(r['code'] == 50027):
            Mysql.query("DELETE FROM webhooks WHERE id = %s", (webhook['id']))
            return render_template('message.html', title="Информация", status="info", msg="Вебхук был удалён с сервера. Запись удалена из БД")
        else: return render_template('message.html', title="Информация", status="info", msg=f"Получен неизвестный код {r['code']}. Никаких действий не выполнено, обратитесь к разработчику")
    else:
        r['token'] = None
        return render_template('message.html', status="success", msg="Похоже, что все в порядке.", title="Информация")

@app.route('/admin', methods=['GET'])
@login_required
def admin():
    status = {'bot':subp("systemctl is-failed d0m1tori"), 'notify':subp("systemctl is-failed d0m1tori-notify")}
    count = {'vk':Mysql.query("SELECT COUNT(*) FROM users WHERE notify = 1")['COUNT(*)'], 'vk_chats':Mysql.query("SELECT COUNT(*) FROM chats WHERE notify = 1")['COUNT(*)'], 'ds':Mysql.query("SELECT COUNT(*) FROM webhooks WHERE enabled = 1")['COUNT(*)']}
    return render_template('index.html', user=g.user, title="Панель управления", status=status, count=count)

@app.route('/auth', methods=['GET'])
def auth():
    if(g.user is not None and g.user.is_authenticated == True):
        return redirect(url_for('admin'))
    return render_template('auth.html', title="Авторизация", vk_auth_id=vk_app['id'])

@app.route('/auth/vk', methods=['POST'])
def vk_auth():
    id_ = request.form.get('id')
    expire = request.form.get('expire')
    mid = request.form.get('mid')
    secret = request.form.get('secret')
    sid = request.form.get('sid')
    sig = request.form.get('sig')
    if(id_ is None or expire is None or mid is None or secret is None or sid is None or sig is None): return {"status":"fail"}, 400
    if(hashlib.md5(f"expire={expire}mid={mid}secret={secret}sid={sid}{vk_app['secret']}".encode()).hexdigest() != sig): return {"status":"fail","description":"sig verify failed"}, 400
    res = Mysql.query("SELECT vkid,dostup FROM users WHERE vkid=%s", (id_))
    if(res == None):
        return {"status":"fail", "description":"Этого аккаунта нет в базе."}
    elif(res['dostup'] < 2):
        Mysql.query("INSERT INTO weblog (`user`,`date`,`description`,`type`,`ip`) VALUES (%s,NOW(),%s,%s,%s)", (res['vkid'],f"Неудачный вход. Dostup: {res['dostup']}", 'auth',request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
        return {"status":"fail", "description":"Ваш уровень доступа слишком низок."}
    # mysql_query("INSERT INTO `web_log` (`user`,`ip`,`date`,`country`,`city`,`type`) VALUES (%s,%s,%s,%s,%s,%s)", (res['id'], request.headers['X-Real-IP'], datetime.now().strftime("%H:%M:%S %d.%m.%Y"), request.headers['X-GEOIP2-COUNTRY_NAME'], request.headers['X-GEOIP2-CITY-NAME'], 1))
    login_user(load_user(res['vkid']), remember=True)
    Mysql.query("INSERT INTO weblog (`user`,`date`,`description`,`type`,`ip`) VALUES (%s,NOW(),%s,%s,%s)", (res['vkid'],f"Успешный вход. Dostup: {res['dostup']}", 'auth',request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
    return {"status":"success", "description":"Вы успешно авторизовались!"}

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth'))

@app.route('/admin/send', methods=['POST'])
@login_required
def send_():
    action = request.form.get('action')
    if(action is None): return abort(400)
    if(action == "force"):
        data = send.check_stream(discord['streamer_id'])
        if('error' in data):
            return {"status":"warning", "description":"Сейчас трансляция не ведётся"}
        subp(f"{dir_path}/send.py {discord['streamer_id']}", shell=True)
        Mysql.query("INSERT INTO weblog (`user`,`date`,`description`,`type`,`ip`) VALUES (%s,NOW(),%s,%s,%s)", (res['vkid'],"Запущена обычная рассылка", 'stream_send',request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
        return {"status":"success", "description":"Рассылка запущена"}
    elif(action == "custom"):
        text = request.form.get('text')
        ds = request.form.get('ds')
        vk = request.form.get('vk')
        post_vk = request.form.get('post_vk')
        if(text is None or ds is None or vk is None): return abort(400)
        a = {'true':1,'false':0};ds = a[ds]; vk = a[vk]; post_vk = a[post_vk]
        text = text.strip()
        if(text == ''): return {"status":"warning", "description":"Сообщение не может быть пустым"}
        if(ds == 0 and vk == 0 and post_vk == 0): return {"status":"warning", "description":"Выберите как минимум один способ рассылки"}
        if(len(text) > 1000): return {"status":"warning", "description":"Размер сообщения не может быть больше 1000 символов"}
        if(vk == 1 and post_vk == 1):
            send.send_vk(None, text, '', True, True)
        elif(vk == 0 and post_vk == 1):
            send.send_vk(None, text, '', True, False)
        elif(vk == 1 and post_vk == 0):
            send.send_vk(None, text, '', False, True)
        if(ds == 1):
            send.send_ds('', text, '', True)
        Mysql.query("INSERT INTO weblog (`user`,`date`,`description`,`type`,`text`,`ip`) VALUES (%s,NOW(),%s,%s,%s)", (res['vkid'],f"Запущена кастомная рассылка. vk:{vk}, post_vk:{post_vk}, ds:{ds}", 'custom_send', text,request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
        return {"status":"success", "description":"Рассылка успешно проведена"}

if(__name__ == '__main__'):
    Mysql = Methods.Mysql()
    # app.run('127.0.0.254', port=5008, debug=True)
    from waitress import serve
    serve(app, host="127.0.0.254", port=5008)
    Mysql.close()
