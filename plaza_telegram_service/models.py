from sqlalchemy import (
    Column, BigInteger, Integer, String, MetaData, Column, ForeignKey, UniqueConstraint, Table, Text,
)

metadata = MetaData()

TelegramUsers = Table(
    'TELEGRAM_USERS', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('telegram_user_id', BigInteger))

TelegramRooms = Table(
    'TELEGRAM_ROOMS', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('telegram_room_id', BigInteger, unique=True),
    Column('room_name', Text))

TelegramUsersInRooms = Table(
    'TELEGRAM_USERS_IN_ROOMS', metadata,
    Column('telegram_id', Integer, ForeignKey('TELEGRAM_USERS.id'), primary_key=True),
    Column('room_id', Integer, ForeignKey('TELEGRAM_ROOMS.id'), primary_key=True),
    __table_args__=(UniqueConstraint('telegram_id', 'room_id')))

PlazaUsers = Table(
    'PLAZA_USERS', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('plaza_user_id', String(36), unique=True))

PlazaUsersInTelegram = Table(
    'PLAZA_USERS_IN_TELEGRAM', metadata,
    Column('plaza_id', Integer, ForeignKey('PLAZA_USERS.id'), primary_key=True),
    Column('telegram_id', Integer, ForeignKey('TELEGRAM_USERS.id'), primary_key=True),
    __table_args__=(UniqueConstraint('plaza_id', 'telegram_id')))
