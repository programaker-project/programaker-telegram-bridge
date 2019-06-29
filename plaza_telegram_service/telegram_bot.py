import logging

from telegram.ext import Updater

class TelegramBot:
    def __init__(self, bot_token, bot_name):
        self.bot_token = bot_token
        self.bot_name = bot_name

        self.on_message = None
        self.handler = None
        self.updater = Updater(token=self.bot_token)

    def start(self):
        self.updater.start_polling()

    def on_exception(self, exception):
        logging.error(repr(exception))
