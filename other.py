import vk, os
import config

session = vk.Session(access_token=config.access_token)
api = vk.API(session, v='5.124', lang='ru')
dir_path = os.path.dirname(os.path.realpath(__file__))