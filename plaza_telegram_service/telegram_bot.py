import os
import logging
import threading
import traceback

from telegram.bot import Bot

POLLING_TIME = 10

class BotRunnerThread(threading.Thread):
    def __init__(self, bot, on_update):
        threading.Thread.__init__(self)
        self.stopped = True
        self.bot = bot
        self.on_update = on_update

    def start(self):
        self.stopped = False
        threading.Thread.start(self)

    def run(self):
        try:
            self.inner_loop()
        except:
            logging.fatal("Broken inner loop: {}".format(traceback.format_exc()))

        os._exit(1)  # Stop the bridge immediately if this is done *by whatever reason*

    def inner_loop(self):
        update_offset = 0
        while not self.stopped:
            updates = self.bot.get_updates(offset=update_offset,
                                           timeout=POLLING_TIME)
            for update in updates:
                self.on_update(update)
                if update.update_id >= update_offset:
                    update_offset = update.update_id + 1


class TelegramBot:
    def __init__(self, bot_token, bot_name):
        self.bot_token = bot_token
        self.bot_name = bot_name

        self.on_message = None
        self.bot = Bot(token=bot_token)
        self.thread = BotRunnerThread(self.bot, self.on_update)

    def start(self):
        self.thread.start()

    def send(self, chat_id, message):
        self.bot.send_message(chat_id=chat_id, text=message)

    def on_update(self, update):
        logging.info("Update: {}".format(update))
        if self.on_message is None:
            return

        self.on_message(update)

    def on_exception(self, exception):
        logging.error(repr(exception))
