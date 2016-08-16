import sqlite3
import base64
from itsdangerous import TimedSerializer, SignatureExpired, BadSignature
from flask import request, current_app
from flask_login import UserMixin
from hashlib import sha256
from eve.auth import TokenAuth
from config import reporting_app_config as cfg
from egcg_core.rest_communication import Communicator

_serialiser = None
user_db = sqlite3.connect(cfg['user_db'])
cursor = user_db.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id text UNIQUE, pw_hash text UNIQUE, login_token text)')


class User(UserMixin):
    username = None
    pw = None
    _communicator = None

    def __init__(self, uid):
        self.username = uid
        if self.exists():
            self.username, self.pw = self.db_record()

    @staticmethod
    def get(uid):
        cursor.execute('SELECT id FROM users WHERE id=?', (uid,))
        r = cursor.fetchone()
        if check_login_token(get_login_token()) == uid:
            return User(r[0])

    def get_id(self):
        return self.username

    def get_auth_token(self):
        return TimedSerializer(current_app.secret_key).dumps(self.username)

    def exists(self):
        cursor.execute('SELECT count(id) FROM users WHERE id=?', (self.username,))
        return cursor.fetchone()[0] == 1

    def db_record(self):
        cursor.execute('SELECT * FROM users WHERE id=?', (self.username,))
        return cursor.fetchone()

    def match_passwords(self, pw_hash):
        return pw_hash == self.pw

    @property
    def comm(self):
        if self._communicator is None:
            self._communicator = Communicator(get_login_token(), cfg['rest_api'])
        return self._communicator


def hash_pw(text):
    return sha256(text.encode()).digest()


def encode_string(text):
    return base64.b64encode(text.encode()).decode('utf-8')


def get_login_token():
    return encode_string(request.cookies.get('remember_token'))


def check_user_auth(username, pw):
    u = User(username)
    return u.exists() and u.match_passwords(hash_pw(pw))


def check_login_token(token_hash):
    dc_token = base64.b64decode(token_hash)
    try:
        return TimedSerializer(current_app.secret_key).loads(dc_token, max_age=cfg.get('user_timeout', 7200))
    except (SignatureExpired, BadSignature):
        return None


def update_user(username, field, new_value):
    cursor.execute('UPDATE users SET %s=? WHERE id=?' % field, (new_value, username))
    user_db.commit()


def change_pw(username, old_pw, new_pw):
    if check_user_auth(username, old_pw):
        update_user(username, 'pw_hash', hash_pw(new_pw))
        return True
    return False


class DualAuth(TokenAuth):
    """Allows authentication by matching a username/password or a login token"""

    def authorized(self, allowed_roles, resource, method):
        if hasattr(request.authorization, 'username'):
            a = request.authorization
            return a and check_user_auth(a.username, a.password)

        elif request.headers.get('Authorization'):
            a = request.headers.get('Authorization').strip()
            auth_type, a = a.split(' ')
            if auth_type.lower() == 'token':
                return a and self.check_auth(a, allowed_roles, resource, method)

    def check_auth(self, token_hash, allowed_roles, resource, method):
        return check_login_token(token_hash)


def admin_users():
    from argparse import ArgumentParser
    a = ArgumentParser()
    for op in ('add', 'remove', 'reset'):
        a.add_argument('--' + op, nargs='+', type=str, default=())
    args = a.parse_args()

    def _add_user(username):
        cursor.execute('INSERT INTO users VALUES (?, ?, ?)', (username, hash_pw(username), None))
        user_db.commit()

    def _remove_user(username):
        cursor.execute('DELETE FROM users WHERE id=?', (username,))
        user_db.commit()

    for u in args.add:
        _add_user(u)

    for u in args.remove:
        _remove_user(u)

    for u in args.reset:
        _remove_user(u)
        _add_user(u)


if __name__ == '__main__':
    print('Using database at ' + cfg['user_db'])
    admin_users()
