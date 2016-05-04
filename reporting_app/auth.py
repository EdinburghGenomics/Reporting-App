import sqlite3
from config import reporting_app_config as cfg
from flask_login import UserMixin
from hashlib import sha256

user_db = sqlite3.connect(cfg['user_db'])
cursor = user_db.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id text UNIQUE, pw_hash text UNIQUE)')


class User(UserMixin):
    def __init__(self, uid):
        self.id = uid

    def get_id(self):
        return self.id


def hash_pw(text):
    return sha256(text.encode()).digest()


def match_passwords(username, pw):
    obs = hash_pw(pw)
    exp = get_user(username)[1]
    return obs == exp


def get_user(username):
    cursor.execute('SELECT * FROM users WHERE id=?', (username,))
    return cursor.fetchone()


def add_user(username, initial_pw='a_pw'):
    cursor.execute('INSERT INTO users VALUES (?, ?)', (username, hash_pw(initial_pw)))
    user_db.commit()


def change_pw(username, old_pw, new_pw):
    if not match_passwords(username, old_pw):
        return None
    new_pw = hash_pw(new_pw)
    cursor.execute('UPDATE USERS SET pw_hash=? WHERE id=?', (new_pw, username))
    user_db.commit()
