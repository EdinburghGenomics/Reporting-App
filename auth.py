import sqlite3
from config import reporting_app_config as cfg
from flask_login import UserMixin
from hashlib import sha256
from base64 import b64encode

user_db = sqlite3.connect(cfg['user_db'])
cursor = user_db.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id text UNIQUE, pw_hash text UNIQUE, api_token text)')


class User(UserMixin):
    def __init__(self, uid, api_token=None):
        self.id = uid
        if api_token:
            self.api_token = api_token
            update_user(self.id, 'api_token', self.api_token)
        else:
            self.api_token = get_user(self.id)[2]

    def get_id(self):
        return self.id

    def erase_token(self):
        update_user(self.id, 'api_token', None)


def hash_pw(text):
    return sha256(text.encode()).digest()


def encode_string(text):
    return b64encode(text.encode()).decode()


def match_passwords(username, pw):
    obs = hash_pw(pw)
    exp = get_user(username)[1]
    return obs == exp


def get_user(username):
    cursor.execute('SELECT * FROM users WHERE id=?', (username,))
    return cursor.fetchone()


def add_user(username, initial_pw='a_pw'):
    cursor.execute('INSERT INTO users VALUES (?, ?, ?)', (username, hash_pw(initial_pw), None))
    user_db.commit()


def update_user(username, field, new_value):
    cursor.execute('UPDATE users SET %s=? WHERE id=?' % field, (new_value, username))
    user_db.commit()


def change_pw(username, old_pw, new_pw):
    if match_passwords(username, old_pw):
        update_user(username, 'pw_hash', hash_pw(new_pw))
