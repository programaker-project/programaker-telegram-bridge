import asyncio
import logging
import sys
from plaza_service import (
    PlazaService,
    ServiceConfiguration,
    MessageBasedServiceRegistration,
    ServiceBlock, ServiceTriggerBlock,
    BlockArgument, DynamicBlockArgument, VariableBlockArgument,
    BlockType, BlockContext,
)
from . import config

class Registerer(MessageBasedServiceRegistration):
    def __init__(self, bot, *args, **kwargs):
        MessageBasedServiceRegistration.__init__(self, *args, **kwargs)
        self.bot = bot

    def get_call_to_action_text(self, extra_data):
        if not extra_data:
            return ('Just greet <a href="https://telegram.me/{bot_name}">{bot_name}</a>'
                    .format(bot_name=self.bot.bot_name))
        return ('Send the following to <a href="https://telegram.me/{bot_name}">{bot_name}</a>'
                '<console>/register {user_id}</console>'
                .format(bot_name=self.bot.bot_name, user_id=extra_data.user_id))


class TelegramService(PlazaService):
    def __init__(self, bot, storage, bridge_endpoint):
        PlazaService.__init__(self, bridge_endpoint)
        self.storage = storage
        self.SUPPORTED_FUNCTIONS = {
        }
        self.bot = bot
        self.bot.handler = self
        self.message_received_event = asyncio.Event()
        self.registerer = Registerer(self.bot, self)
        self.bot.start()

    def on_new_message(self, update):
        if 'message' not in dir(update):
            return

        user = update.message.from_user.id
        room = update.message.chat.id
        if not self.storage.is_telegram_user_registered(user):
            self._on_non_registered_event(user, room, update)
        else:
            PlazaService.emit_event_sync(
                self,
                to_user=self.storage.get_plaza_user_from_telegram(
                    user),
                key="on_new_message",
                content=update.message.text,
                event=update.to_dict())
            self.last_message = (room, update)

    def _on_non_registered_event(self, user, room, update):
        if 'text' not in dir(update.message):
            return

        msg = update.message.text
        prefix = '/register '
        if msg.startswith(prefix):
            register_id = msg[len(prefix):]
            self.storage.register_user(user, register_id)
            self.bot.send(room,
                          "Welcome! You're registered!\n"
                          "Now you can use this bot in your programs.")
        else:
            self.bot.send(room,
                          "Hi! I'm a bot in the making, ask @{maintainer} for more info if you want to know how to program me ;)."
                          .format(maintainer=config.get_maintainer_telegram_handle()))

    async def handle_data_callback(self, callback_name, extra_data):
        logging.info("GET {} # {}".format(
            callback_name, extra_data.user_id))
        results = {}
        for user in self.storage.get_telegram_users(extra_data.user_id):
            for room in self.members[user]:
                results[room.room_id] = {"name": room.display_name}

        return results

    async def handle_call(self, function_name, arguments, extra_data):
        logging.info("{}({}) # {}".format(
            function_name, ", ".join(arguments), extra_data.user_id))
        return await self.SUPPORTED_FUNCTIONS[function_name](extra_data, *arguments)

    def handle_configuration(self):
        return ServiceConfiguration(
            service_name="Telegram",
            is_public=True,
            registration=self.registerer,
            blocks=[
                ServiceTriggerBlock(
                    id="on_new_message",
                    function_name="on_new_message",
                    message="When received any message. Set %1",
                    arguments=[
                        VariableBlockArgument(),
                    ],
                    save_to=BlockContext.ARGUMENTS[0],
                ),
            ],
        )
