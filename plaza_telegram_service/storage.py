import re
import os
from xdg import XDG_DATA_HOME

import sqlalchemy

from . import models

DB_PATH_ENV = 'PLAZA_TELEGRAM_BRIDGE_DB_PATH'

if os.getenv(DB_PATH_ENV, None) is None:
    _DATA_DIRECTORY = os.path.join(XDG_DATA_HOME, "plaza", "bridges", "telegram")
    CONNECTION_STRING = "sqlite:///{}".format(os.path.join(_DATA_DIRECTORY, 'db.sqlite3'))
else:
    CONNECTION_STRING = os.getenv(DB_PATH_ENV)


class EngineContext:
    def __init__(self, engine):
        self.engine = engine
        self.connection = None

    def __enter__(self):
        self.connection = self.engine.connect()
        return self.connection

    def __exit__(self, exc_type, exc_value, tb):
        self.connection.close()

class StorageEngine:
    def __init__(self, engine):
        self.engine = engine

    def _connect_db(self):
        return EngineContext(self.engine)

    def is_telegram_user_registered(self, user_id):
        with self._connect_db() as conn:
            result = conn.execute(
                sqlalchemy.select([
                    models.TelegramUsers.c.id,
                ])
                .where(models.TelegramUsers.c.telegram_user_id == user_id)
            ).fetchone()
            return result is not None

    def get_plaza_users_from_telegram(self, user_id):
        with self._connect_db() as conn:
            join = (sqlalchemy.join(models.PlazaUsers, models.PlazaUsersInTelegram,
                                    models.PlazaUsers.c.id
                                    == models.PlazaUsersInTelegram.c.plaza_id)
                    .join(models.TelegramUsers,
                          models.PlazaUsersInTelegram.c.telegram_id == models.TelegramUsers.c.id))

            results = conn.execute(
                sqlalchemy.select([
                    models.PlazaUsers.c.plaza_user_id,
                ])
                .select_from(join)
                .where(models.TelegramUsers.c.telegram_user_id == user_id)
            ).fetchall()

            return map(lambda result: result.plaza_user_id, results)

    def register_user(self, telegram_user, plaza_user):
        with self._connect_db() as conn:
            telegram_id = self._get_or_add_telegram_user(conn, telegram_user)
            plaza_id = self._get_or_add_plaza_user(conn, plaza_user)

            check = conn.execute(
                sqlalchemy.select([models.PlazaUsersInTelegram.c.plaza_id])
                .where(
                    sqlalchemy.and_(
                        models.PlazaUsersInTelegram.c.plaza_id == plaza_id,
                        models.PlazaUsersInTelegram.c.telegram_id == telegram_id))
            ).fetchone()

            if check is not None:
                return

            insert = models.PlazaUsersInTelegram.insert().values(plaza_id=plaza_id,
                                                                 telegram_id=telegram_id)
            conn.execute(insert)

    def add_user_to_room(self, telegram_user, telegram_room, room_name):
        with self._connect_db() as conn:
            telegram_id = self._get_or_add_telegram_user(conn, telegram_user)
            room_id = self._get_or_add_telegram_room(conn, telegram_room, room_name)

            check = conn.execute(
                sqlalchemy.select([models.TelegramUsersInRooms.c.telegram_id])
                .where(
                    sqlalchemy.and_(
                        models.TelegramUsersInRooms.c.telegram_id == telegram_id,
                        models.TelegramUsersInRooms.c.room_id == room_id))
            ).fetchone()

            if check is not None:
                return

            insert = models.TelegramUsersInRooms.insert().values(telegram_id=telegram_id,
                                                                 room_id=room_id)
            conn.execute(insert)

    def get_telegram_users(self, plaza_user):
        with self._connect_db() as conn:
            plaza_id = self._get_or_add_plaza_user(conn, plaza_user)
            join = sqlalchemy.join(models.TelegramUsers, models.PlazaUsersInTelegram,
                                   models.TelegramUsers.c.id
                                   == models.PlazaUsersInTelegram.c.telegram_id)

            results = conn.execute(
                sqlalchemy.select([
                    models.TelegramUsers.c.telegram_user_id,
                ])
                .select_from(join)
                .where(models.PlazaUsersInTelegram.c.plaza_id == plaza_id)
            ).fetchall()

            return [
                row[0]
                for row in results
            ]

    def get_telegram_rooms_for_plaza_user(self, plaza_user):
        with self._connect_db() as conn:
            plaza_id = self._get_or_add_plaza_user(conn, plaza_user)

            join = models.TelegramUsers.join(
                models.PlazaUsersInTelegram,
                models.TelegramUsers.c.id == models.PlazaUsersInTelegram.c.telegram_id
            ).join(
                models.TelegramUsersInRooms,
                models.TelegramUsers.c.id == models.TelegramUsersInRooms.c.telegram_id
            ).join(
                models.TelegramRooms,
                models.TelegramUsersInRooms.c.room_id == models.TelegramRooms.c.id
            )

            results = conn.execute(
                sqlalchemy.select([
                    models.TelegramUsers.c.telegram_user_id,
                    models.TelegramRooms.c.telegram_room_id,
                    models.TelegramRooms.c.room_name,
                ])
                .select_from(join)
                .where(models.PlazaUsersInTelegram.c.plaza_id == plaza_id)
            ).fetchall()
            return results


    def _get_or_add_telegram_user(self, conn, telegram_user):
        check = conn.execute(
            sqlalchemy.select([models.TelegramUsers.c.id])
            .where(models.TelegramUsers.c.telegram_user_id == telegram_user)
        ).fetchone()

        if check is not None:
            return check.id

        insert = models.TelegramUsers.insert().values(telegram_user_id=telegram_user)
        result = conn.execute(insert)
        return result.inserted_primary_key[0]

    def _get_or_add_telegram_room(self, conn, telegram_room, room_name):
        check = conn.execute(
            sqlalchemy.select([models.TelegramRooms.c.id])
            .where(models.TelegramRooms.c.telegram_room_id == telegram_room)
        ).fetchone()

        if check is not None:
            return check.id

        insert = models.TelegramRooms.insert().values(telegram_room_id=telegram_room,
                                                      room_name=room_name)
        result = conn.execute(insert)
        return result.inserted_primary_key[0]

    def _get_or_add_plaza_user(self, conn, plaza_user):
        check = conn.execute(
            sqlalchemy.select([models.PlazaUsers.c.id])
            .where(models.PlazaUsers.c.plaza_user_id == plaza_user)
        ).fetchone()

        if check is not None:
            return check.id

        insert = models.PlazaUsers.insert().values(plaza_user_id=plaza_user)
        result = conn.execute(insert)
        return result.inserted_primary_key[0]

def get_engine():
    # Create path to SQLite file, if its needed.
    if CONNECTION_STRING.startswith('sqlite'):
        db_file = re.sub("sqlite.*:///", "", CONNECTION_STRING)
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

    engine = sqlalchemy.create_engine(CONNECTION_STRING, echo=True)
    metadata = models.metadata
    metadata.create_all(engine)

    return StorageEngine(engine)
