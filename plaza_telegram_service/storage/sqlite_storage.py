import os
import sqlite3
from xdg import XDG_DATA_HOME

DATA_DIRECTORY = os.path.join(XDG_DATA_HOME, 'plaza', 'bridges', 'telegram')
DEFAULT_PATH = os.path.join(DATA_DIRECTORY, 'db.sqlite3')


class DBContext:
    def __init__(self, db, close_on_exit=True):
        self.db = db
        self.close_on_exit = close_on_exit

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, tb):
        if self.close_on_exit:
            self.db.close()


class SqliteStorage:
    def __init__(self, path, multithread=True):
        self.path = path
        self.db = None
        self.multithread = multithread
        self._create_db_if_not_exists()

    def _open_db(self):
        if not self.multithread:
            if self.db is None:
                self.db = sqlite3.connect(self.path)
                self.db.execute('PRAGMA foreign_keys = ON;')
            db = self.db
        else:
            db = sqlite3.connect(self.path)
            db.execute('PRAGMA foreign_keys = ON;')

        return DBContext(db, close_on_exit=not self.multithread)

    def _create_db_if_not_exists(self):
        os.makedirs(DATA_DIRECTORY, exist_ok=True)
        with self._open_db() as db:
            c = db.cursor()
            c.execute('''
            CREATE TABLE IF NOT EXISTS TELEGRAM_USERS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id VARCHAR(256) UNIQUE
            );
            ''')

            c.execute('''
            CREATE TABLE IF NOT EXISTS PLAZA_USERS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plaza_user_id VARCHAR(36) UNIQUE
            );
            ''')

            c.execute('''
            CREATE TABLE IF NOT EXISTS PLAZA_USERS_IN_TELEGRAM (
                plaza_id INTEGER,
                telegram_id INTEGER,
                UNIQUE(plaza_id, telegram_id),
                FOREIGN KEY(plaza_id) REFERENCES PLAZA_USERS(id),
                FOREIGN KEY(telegram_id) REFERENCES TELEGRAM_USERS(id)
            );
            ''')
            db.commit()
            c.close()

    def is_telegram_user_registered(self, user_id):
        with self._open_db() as db:
            c = db.cursor()
            c.execute('''
            SELECT count(1)
            FROM TELEGRAM_USERS
            WHERE telegram_user_id=?
            ;
            ''', (user_id,))
            result = c.fetchone()[0]

            c.close()

            return result > 0

    def get_plaza_user_from_telegram(self, user_id):
        with self._open_db() as db:
            c = db.cursor()
            c.execute('''
            SELECT plaza_user_id
            FROM PLAZA_USERS as p
            JOIN PLAZA_USERS_IN_TELEGRAM as puit
            ON puit.plaza_id = p.id
            JOIN TELEGRAM_USERS as t
            ON puit.telegram_id = m.id
            WHERE t.telegram_user_id=?
            ;
            ''', (user_id,))
            results = c.fetchall()

            c.close()
            assert 0 <= len(results) <= 1
            if len(results) == 0:
                raise Exception('User (telegram:{}) not found'.format(user_id))
            return results[0][0]

    def _get_or_add_telegram_user(self, cursor, telegram_user):
        cursor.execute('''
        SELECT id
        FROM TELEGRAM_USERS
        WHERE telegram_user_id=?
        ;
        ''', (telegram_user,))

        results = cursor.fetchall()
        if len(results) == 0:  # New user
            cursor.execute('''
            INSERT INTO TELEGRAM_USERS (telegram_user_id) VALUES(?);
            ''', (telegram_user,))
            return cursor.lastrowid
        elif len(results) == 1:  # Existing user
            return results[0][0]
        else:  # This shouldn't happen
            raise Exception(
                'Integrity error, query by UNIQUE returned multiple values: {}'
                .format(cursor.rowcount))

    def _get_or_add_plaza_user(self, cursor, plaza_user):
        cursor.execute('''
        SELECT id
        FROM PLAZA_USERS
        WHERE plaza_user_id=?
        ;
        ''', (plaza_user,))

        results = cursor.fetchall()
        if len(results) == 0:  # New user
            cursor.execute('''
            INSERT INTO PLAZA_USERS (plaza_user_id) VALUES(?);
            ''', (plaza_user,))
            return cursor.lastrowid
        elif len(results) == 1:  # Existing user
            return results[0][0]
        else:  # This shouldn't happen
            raise Exception(
                'Integrity error, query by UNIQUE returned multiple values: {}'
                .format(cursor.rowcount))

    def register_user(self, telegram_user, plaza_user):
        with self._open_db() as db:
            c = db.cursor()
            telegram_id = self._get_or_add_telegram_user(c, telegram_user)
            plaza_id = self._get_or_add_plaza_user(c, plaza_user)
            c.execute('''
            INSERT OR REPLACE INTO
            PLAZA_USERS_IN_TELEGRAM (plaza_id, telegram_id)
            VALUES (?, ?)
            ''', (plaza_id, telegram_id))
            c.close()
            db.commit()

    def get_telegram_users(self, plaza_user):
        with self._open_db() as db:
            c = db.cursor()
            plaza_id = self._get_or_add_plaza_user(c, plaza_user)
            c.execute('''
            SELECT telegram_user_id
            FROM TELEGRAM_USERS m
            JOIN PLAZA_USERS_IN_TELEGRAM pim
            ON m.id=pim.telegram_id
            WHERE pim.plaza_id=?
            ;
            ''', (plaza_id,))
            results = c.fetchall()
            c.close()
            return [row[0] for row in results]


def get_default():
    return SqliteStorage(DEFAULT_PATH)
