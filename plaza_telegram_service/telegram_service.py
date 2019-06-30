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
            "send_message": self.send_message,
        }
        self.bot = bot
        self.bot.handler = self
        self.message_received_event = asyncio.Event()
        self.registerer = Registerer(self.bot, self)
        self.bot.start()

    def get_chat_name(self, chat):
        if chat.title is not None:
            return chat.title
        if chat.username is not None:
            return chat.username
        logging.error("Unknown chat name from: {}".format(chat))
        return "chat-{}".format(chat.id)

    def on_new_message(self, update):
        if update.message is None:
            return

        user = update.message.from_user.id
        room = update.message.chat.id

        # Route the message depending on if the user is already registered
        if not self.storage.is_telegram_user_registered(user):
            self._on_non_registered_event(user, room, update)
        else:
            # If the user is registered, allow it to send messages to this chat
            chat_name = self.get_chat_name(update.message.chat)
            self.storage.add_user_to_room(user, room, room_name=chat_name)

            # And send the event about this message reception
            PlazaService.emit_event_sync(
                self,
                to_user=self.storage.get_plaza_user_from_telegram(
                    user),
                key="on_new_message",
                content=update.message.text,
                event=update.to_dict())

    def _on_non_registered_event(self, user, room, update):
        if update.message.text is None:
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
        for (_telegram_user, telegram_room_id, telegram_room_name) in (
                self.storage.get_telegram_rooms_for_plaza_user(extra_data.user_id)):
            results[telegram_room_id] = {"name": telegram_room_name}

        return results

    async def send_message(self, extra_data, room_id, message):
        self.bot.send(room_id, message)

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
                ServiceBlock(
                    id="send_message",
                    function_name="send_message",
                    message="On channel %1 say %2",
                    arguments=[
                        DynamicBlockArgument(str, "get_available_channels"),
                        BlockArgument(str, "Hello"),
                    ],
                    block_type=BlockType.OPERATION,
                    block_result_type=None,
                ),
                ServiceTriggerBlock(
                    id="on_new_message",
                    function_name="on_new_message",
                    message="When received any message. Set %1",
                    arguments=[
                        VariableBlockArgument(),
                    ],
                    save_to=BlockContext.ARGUMENTS[0],
                ),
                ServiceTriggerBlock(
                    id="on_command",
                    function_name="on_command",
                    message="When received %1",
                    arguments=[
                        BlockArgument(str, "/start"),
                    ],
                    expected_value=BlockContext.ARGUMENTS[0],
                    key="on_new_message",
                ),
            ],
        )
