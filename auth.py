import sqlite3
import base64
import itsdangerous
from flask import request, current_app
from flask_login import UserMixin
from hashlib import sha256
from eve.auth import TokenAuth
from config import reporting_app_config as cfg

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
    return base64.b64encode(text.encode()).decode('utf-8')


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


class DualAuth(TokenAuth):
    """Allows authentication by matching a username/password or an API token"""

    def authorized(self, allowed_roles, resource, method):
        if hasattr(request.authorization, 'username'):
            _auth = request.authorization
            return _auth and match_passwords(_auth.username, _auth.password)

        elif request.headers.get('Authorization'):
            _auth = request.headers.get('Authorization').strip()
            auth_type, _auth = _auth.split(' ')
            if auth_type.lower() == 'token':
                return _auth and self.check_auth(_auth, allowed_roles, resource, method)

    def check_auth(self, token_hash, allowed_roles, resource, method):
        s = itsdangerous.TimedSerializer(current_app.secret_key)
        dc_token = base64.b64decode(token_hash)
        try:
            return s.loads(dc_token, max_age=7200).get('token')
        except (itsdangerous.SignatureExpired, itsdangerous.BadSignature):
            return None
