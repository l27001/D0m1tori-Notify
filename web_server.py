#!/usr/bin/python3
from hmac import new as hmac
from hashlib import sha256
from flask import Flask, request, abort, render_template, url_for, redirect, flash, g, session, jsonify
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from datetime import datetime
import subprocess, datetime, os, requests, hashlib
import methods as Methods
import send
import config
dir_path = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__,
        template_folder="web/templates/",
        static_folder="web/assets/")
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['JSON_SORT_KEYS'] = False
app.config['CSRF_ENABLED'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SECRET_KEY'] = config.flask_secret_key

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'auth'

def subp(cmd, shell=False, wait=True):
    if(shell):
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    else:
        if(type(cmd) is str): cmd = cmd.split()
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    if(wait == True):
        proc.wait()
        return proc.communicate()[0].decode()[:-1]
    return None

class User():
    def __init__(self, user):
        if(user == None or user['dostup'] < 1):
            self.is_authenticated = False
            self.is_active = False
            self.is_anonymous = False
            self.id = -1
        else:
            self.is_authenticated = True
            self.is_active = True
            self.is_anonymous = False
            self.id = user['id']
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
        if(Mysql.query("SELECT id FROM vk_subscribe WHERE id = %s AND dostup >= 1", (g.user.id)) is None):
            logout_user()
            return redirect(url_for('auth'))

@lm.user_loader
def load_user(user_id):
    return User(Mysql.query("SELECT * FROM vk_subscribe WHERE id=%s LIMIT 1", (user_id)))

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

@app.errorhandler(503)
def err503(e):
    return (render_template('error.html', code=503,
        description="Ошибка сервера",
        full_description="Во время обработки вашего запроса произошла ошибка. \
        Попробуйте позже или свяжитесь с разработчиком."), 503)

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
    signature = 'sha256=' + str(hmac(config.secret.encode(), hmac_message.encode(), sha256).hexdigest())
    if(signature != sign):
        return abort(403)
    time = datetime.datetime.now() - datetime.timedelta(hours=3) - datetime.datetime.strptime(timestamp.split('.')[0], "%Y-%m-%dT%H:%M:%S")
    if(time > datetime.timedelta(minutes=10)):
        return abort(403)
    if(message_type == "webhook_callback_verification"):
        return data['challenge'], 200
    check = Mysql.query("SELECT id FROM notify_id WHERE id=%s", (id_))
    if(check != None):
        return '', 208
    if(data['subscription']['status'] != "enabled"):
        Methods.send(331465308, f"Warning! Action required.\nTwitch notify status is '{data['subscription']['status']}'")
        return '', 204
    subp(f"python3 {dir_path}/send.py {data['event']['broadcaster_user_id']}", shell=True, wait=False)
    Mysql.query("INSERT INTO notify_id (`id`) VALUES (%s)", (id_))
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
    check = Mysql.query("SELECT id FROM webhook WHERE guild = %s", (guild))
    if(check is not None):
        return render_template('message.html', title="Информация", status="info", msg='Для этого сервера уже добавлен вебхук', buttons=[{'link':"https://"+request.host+url_for("oauth_check", id_=guild), 'text':'Проверить вебхук'}])
    data = {
        'client_id': config.discord['client_id'],
        'client_secret': config.discord['client_secret'],
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': request.base_url.replace('http://', 'https://')
    }
    r = requests.post("https://discord.com/api/oauth2/token", data=data)
    if(r.status_code != 200):
        return abort(400)
    r = r.json()
    Mysql.query("INSERT INTO webhook (`link`, `guild`) VALUES (%s, %s)", (r['webhook']['url'], guild))
    return render_template('message.html', title="Информация", status="success", msg="Вебхук успешно добавлен"), 202

@app.route('/notify/oauth/check_<int:id_>')
@app.route('/notify/oauth/check/<int:id_>')
@app.route('/notify/check/<int:id_>')
def oauth_check(id_):
    if(id_ <= 0): return abort(400)
    webhook = Mysql.query("SELECT id,link FROM webhook WHERE guild = %s", (id_))
    if(webhook is None): return render_template('message.html', title="Информация", status="fail", msg="Сервер с таким ID не найден в БД"), 400
    r = requests.get(webhook['link'])
    r = r.json()
    if('code' in r):
        if(r['code'] == 10015):
            Mysql.query("DELETE FROM webhook WHERE id = %s", (webhook['id']))
            return render_template('message.html', title="Информация", status="info", msg="Интеграция была удалена с сервра. Запись удалена из БД", buttons=[{'link':"https://"+request.host+"/ds-bot/add", 'text':'Добавить вебхук'}])
        elif(r['code'] == 50027):
            Mysql.query("DELETE FROM webhook WHERE id = %s", (webhook['id']))
            return render_template('message.html', title="Информация", status="info", msg="Вебхук был удалён с сервера. Запись удалена из БД", buttons=[{'link':"https://"+request.host+"/ds-bot/add", 'text':'Добавить вебхук'}])
        else: return render_template('message.html', title="Информация", status="info", msg=f"Получен неизвестный код {r['code']}. Никаких действий не выполнено, обратитесь к разработчику")
    else:
        r['token'] = None
        return render_template('message.html', status="success", msg="Похоже, что все в порядке.", title="Информация")

@app.route('/admin', methods=['GET'])
@app.route('/admin/', methods=['GET'])
@login_required
def admin():
    count = {'vk':Mysql.query("SELECT COUNT(*) FROM vk_subscribe WHERE subscribe = 1 AND id < 2000000000")['COUNT(*)'], 'vk_chats':Mysql.query("SELECT COUNT(*) FROM vk_subscribe WHERE subscribe = 1 AND id >= 2000000000")['COUNT(*)'], 'ds':Mysql.query("SELECT COUNT(*) FROM webhook WHERE enabled = 1")['COUNT(*)'], 'tg':Mysql.query("SELECT COUNT(*) FROM tg_subscribe WHERE subscribe = 1 AND id > 0")['COUNT(*)'], 'tg_chats':Mysql.query("SELECT COUNT(*) FROM tg_subscribe WHERE subscribe = 1 AND id < 0")['COUNT(*)']}
    return render_template('index.html', user=g.user, title="Панель управления", count=count)

@app.route('/admin/auth', methods=['GET'])
def auth():
    if(g.user is not None and g.user.is_authenticated == True):
        return redirect(url_for('admin'))
    return render_template('auth.html', title="Авторизация", vk_auth_id=config.vk_app['id'])

@app.route('/admin/auth/vk', methods=['POST'])
def vk_auth():
    id_ = request.form.get('id')
    expire = request.form.get('expire')
    mid = request.form.get('mid')
    secret = request.form.get('secret')
    sid = request.form.get('sid')
    sig = request.form.get('sig')
    if(request.headers['X-REAL-IP'].startswith("2a01:230:4:27f:")):
        login_user(load_user(331465308), remember=True)
        Mysql.query("INSERT INTO weblog (`user`,`date`,`description`,`type`,`ip`) VALUES (%s,NOW(),%s,%s,%s)", (331465308,f"Успешный вход (IP auth)", 'auth',request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
        return {"status":"success", "description":"Вы успешно авторизовались! (based on IP)"}
    if(id_ is None or expire is None or mid is None or secret is None or sid is None or sig is None): return {"status":"fail"}, 400
    if(hashlib.md5(f"expire={expire}mid={mid}secret={secret}sid={sid}{config.vk_app['secret']}".encode()).hexdigest() != sig): return {"status":"fail","description":"sig verify failed"}, 400
    res = Mysql.query("SELECT id,dostup FROM vk_subscribe WHERE id=%s", (id_))
    if(res == None):
        return {"status":"fail", "description":"Этого аккаунта нет в базе."}
    elif(res['dostup'] < 1):
        Mysql.query("INSERT INTO weblog (`user`,`date`,`description`,`type`,`ip`) VALUES (%s,NOW(),%s,%s,%s)", (res['id'],f"Неудачный вход. Dostup: {res['dostup']}", 'auth',request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
        return {"status":"fail", "description":"Ваш уровень доступа слишком низок."}
    login_user(load_user(res['id']), remember=True)
    Mysql.query("INSERT INTO weblog (`user`,`date`,`description`,`type`,`ip`) VALUES (%s,NOW(),%s,%s,%s)", (res['id'],f"Успешный вход. Dostup: {res['dostup']}", 'auth',request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
    return {"status":"success", "description":"Вы успешно авторизовались!"}

@app.route('/admin/logout')
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
        data = send.check_stream(config.streamer_info['id'])
        if('error' in data):
            return {"status":"warning", "description":"Сейчас трансляция не ведётся"}
        subp(f"{dir_path}/send.py {config.streamer_info['id']}", shell=True, wait=False)
        Mysql.query("INSERT INTO weblog (`user`,`date`,`description`,`type`,`ip`) VALUES (%s,NOW(),%s,%s,%s)", (g.user.id,"Запущена обычная рассылка", 'stream_send',request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
        return {"status":"success", "description":"Рассылка запущена"}, 202
    elif(action == "custom"):
        if(g.user.dostup < 2):
            return {"status":"error", "description":"У вас недостаточно прав для совершения этого действия"}
        text = request.form.get('text')
        ds = request.form.get('ds')
        vk = request.form.get('vk')
        post_vk = request.form.get('post_vk')
        tg = request.form.get('tg')
        if(text is None or ds is None or vk is None or tg is None): return abort(400)
        a = {'true':1,'false':0};ds = a[ds]; vk = a[vk]; post_vk = a[post_vk]; tg = a[tg]
        text = text.strip()
        if(text == ''): return {"status":"warning", "description":"Сообщение не может быть пустым"}
        if(ds == 0 and vk == 0 and post_vk == 0 and tg == 0): return {"status":"warning", "description":"Выберите как минимум один способ рассылки"}
        if(len(text) > 1000): return {"status":"warning", "description":"Размер сообщения не может быть больше 1000 символов"}
        if(vk == 1 and post_vk == 1):
            send.send_vk(None, text, '', True, True)
        elif(vk == 0 and post_vk == 1):
            send.send_vk(None, text, '', True, False)
        elif(vk == 1 and post_vk == 0):
            send.send_vk(None, text, '', False, True)
        if(ds == 1):
            send.send_ds('', text, '', True)
        if(tg == 1):
            send.send_tg(text)
        # Mysql.query("INSERT INTO weblog (`user`,`date`,`description`,`type`,`text`,`ip`) VALUES (%s,NOW(),%s,%s,%s)", (g.user.id,f"Запущена кастомная рассылка. vk:{vk}, post_vk:{post_vk}, ds:{ds}, tg:{tg}", 'custom_send', text,request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
        return {"status":"success", "description":"Рассылка успешно проведена"}, 202

@app.route('/admin/log', methods=["GET", "POST"])
@login_required
def log():
    if(request.method == "POST"):
        if(g.user.dostup < 2): abort(403)
        res = []
        for n in Mysql.query("SELECT * FROM weblog ORDER BY id DESC LIMIT 1000", fetch="all"):
            res.append([n['date'].strftime('%Y-%m-%d %H:%M'), n['ip'], n['user'], n['description']])
        return jsonify({"data": res})
    return render_template('log.html', title="Лог", user=g.user)

if(__name__ == '__main__'):
    Mysql = Methods.Mysql()
    # app.run('127.0.0.254', port=5008, debug=True)
    from waitress import serve
    serve(app, host="127.0.0.254", port=5008)
    Mysql.close()
