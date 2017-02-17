import sqlite3
import base64
import binascii
import itsdangerous
from flask import request, current_app
from flask_login import UserMixin
from hashlib import sha256
from eve.auth import TokenAuth
from config import reporting_app_config as cfg
from egcg_core.rest_communication import Communicator

_serialiser = None
user_db = sqlite3.connect(cfg['user_db'])
cursor = user_db.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id text UNIQUE, pw_hash text UNIQUE)')


class User(UserMixin):
    username = None
    pw = None
    _communicator = None

    def __init__(self, uid):
        self.username = uid
        if self.exists():
            self.username, self.pw = self.db_record()

    @classmethod
    def get(cls, uid):
        cursor.execute('SELECT id FROM users WHERE id=?', (uid,))
        r = cursor.fetchone()
        if r is None:
            current_app.logger.error("Could not find user '%s' in database", uid)
        if check_login_token(cls.get_login_token()) == uid:
            return User(r[0])

    def get_id(self):
        return self.username

    def get_auth_token(self):
        """Used by flask_login to set cookie/login token."""
        s = itsdangerous.TimedSerializer(current_app.secret_key)
        return encode_string(s.dumps(self.username))

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
            self._communicator = Communicator(self.get_login_token(), cfg['rest_api'])
        return self._communicator

    @staticmethod
    def get_login_token():
        return request.cookies.get('remember_token')


def hash_pw(text):
    return sha256(text.encode()).digest()


def encode_string(text):
    return base64.b64encode(text.encode()).decode('utf-8')


def check_user_auth(username, pw):
    u = User(username)
    return u.exists() and u.match_passwords(hash_pw(pw))


def check_login_token(token_hash):
    try:
        dc_token = base64.b64decode(token_hash)
        s = itsdangerous.TimedSerializer(current_app.secret_key)
        return s.loads(dc_token, max_age=cfg.get('user_timeout', 7200))
    except (itsdangerous.SignatureExpired, itsdangerous.BadSignature):
        return None
    except binascii.Error as e:
        current_app.logger.warning("binascii.Error: '%s' from token hash '%s'", str(e), token_hash)
        return None


def change_pw(username, old_pw, new_pw):
    if check_user_auth(username, old_pw):
        cursor.execute('UPDATE users SET pw_hash=? WHERE id=?', (hash_pw(new_pw), username))
        user_db.commit()
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
    a.add_argument('action', choices=('add', 'remove', 'reset'))
    a.add_argument('username')
    a.add_argument('--password', nargs='?', default=None)
    args = a.parse_args()

    def _add_user(username, password=None):
        cursor.execute('INSERT INTO users VALUES (?, ?)', (username, hash_pw(username or password)))
        user_db.commit()

    def _remove_user(username):
        cursor.execute('DELETE FROM users WHERE id=?', (username,))
        user_db.commit()

    if args.action == 'add':
        _add_user(args.username, args.password)

    elif args.action == 'remove':
        _remove_user(args.username)

    elif args.action == 'reset':
        _remove_user(args.username)
        _add_user(args.username)

    print("Performed action '%s' on user '%s'" % (args.action, args.username))


if __name__ == '__main__':
    print('Using database at ' + cfg['user_db'])
    admin_users()
