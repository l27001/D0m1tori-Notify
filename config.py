### Config for Bot
db = {'host':'HOST', # Database info (mysql)
        'user':'USER',
        'password':'PASSWORD',
        'database':'DATABASE'}

vk_info = {'access_token': 'MY_KEY', 'groupid': '00000', 'url': 'https://api.vk.com/method/'} # vk group data
vk_app = {'id': "00000", 'secret': "MY_KEY"} # vk app for web auth

tmp_dir = "/tmp/MY_AWESOME_BOT" # NO SPACES!
twitch_api = "MY_KEY" # secret_key for twitch auth (get on dev.twitch.tv)
client_id = "MY_ID" # client_id for twitch auth (get on dev.twitch.tv)
secret = "RANDOM_STRING" # Secret string for twitch webhook (needed for create/get info from webhook)
user_token = "MY_KEY" # vk user token for posting on wall
discord = {'client_id': "0000", 'client_secret': "VERY_SECRET"} # Discord bot info
streamer_info = {'id': '123321', 'login': 'AWESOME_GUY'} # twitch streamer info
flask_secret_key = "RANDOM_STRING"

tg_info = {'access_token': 'MY_KEY', 'url':'https://api.telegram.org/'} # Telegram data