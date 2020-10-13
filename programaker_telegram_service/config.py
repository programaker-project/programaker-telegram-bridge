import getpass
import json
import os
from xdg import XDG_CONFIG_HOME

TELEGRAM_BOT_TOKEN_ENV = 'TELEGRAM_BOT_TOKEN'
TELEGRAM_BOT_NAME_ENV = 'TELEGRAM_BOT_NAME'
BRIDGE_ENDPOINT_ENV = 'PLAZA_BRIDGE_ENDPOINT'
MAINTAINER_TELEGRAM_HANDLE_ENV = 'MAINTAINER_TELEGRAM_HANDLE'
DEFAULT_MAINTAINER_TELEGRAM_HANDLE = 'kenkeiras'
AUTH_TOKEN_ENV = 'PLAZA_BRIDGE_AUTH_TOKEN'

TELEGRAM_BOT_TOKEN_INDEX = 'telegram_bot_token'
TELEGRAM_BOT_NAME_INDEX = 'telegram_bot_name'
BRIDGE_ENDPOINT_INDEX = 'plaza_bridge_endpoint'
AUTH_TOKEN_INDEX = 'plaza_authentication_token'

global directory, config_file
directory = os.path.join(XDG_CONFIG_HOME, 'plaza', 'bridges', 'telegram')
config_file = os.path.join(directory, 'config.json')


def _get_config():
    if not os.path.exists(config_file):
        return {}
    with open(config_file, 'rt') as f:
        return json.load(f)


def _save_config(config):
    os.makedirs(directory, exist_ok=True)
    with open(config_file, 'wt') as f:
        return json.dump(config, f)


def get_bot_token():
    # Check if the bot token is defined in an environment variable
    bot_token_env = os.getenv(TELEGRAM_BOT_TOKEN_ENV, None)
    if bot_token_env is not None:
        return bot_token_env

    # If not, request it and save it to a file
    config = _get_config()
    if config.get(TELEGRAM_BOT_TOKEN_INDEX, None) is None:
        config[TELEGRAM_BOT_TOKEN_INDEX] = input('Bot token: ').strip()
        if not config[TELEGRAM_BOT_TOKEN_INDEX]:
            raise Exception('No bot token introduced')
        _save_config(config)
    return config[TELEGRAM_BOT_TOKEN_INDEX]


def get_bot_name():
    # Check if the bot name is defined in an environment variable
    bot_name_env = os.getenv(TELEGRAM_BOT_NAME_ENV, None)
    if bot_name_env is not None:
        return bot_name_env

    # If not, request it and save it to a file
    config = _get_config()
    if config.get(TELEGRAM_BOT_NAME_INDEX, None) is None:
        config[TELEGRAM_BOT_NAME_INDEX] = input('Bot name: ').strip()
        if not config[TELEGRAM_BOT_NAME_INDEX]:
            raise Exception('No bot name introduced')
        _save_config(config)
    return config[TELEGRAM_BOT_NAME_INDEX]


def get_bridge_endpoint():
    # Check if the bridge endpoint is defined in an environment variable
    programaker_bridge_endpoint_env = os.getenv(BRIDGE_ENDPOINT_ENV, None)
    if programaker_bridge_endpoint_env is not None:
        return programaker_bridge_endpoint_env

    # If not, request it and save it to a file
    config = _get_config()
    if config.get(BRIDGE_ENDPOINT_INDEX, None) is None:
        config[BRIDGE_ENDPOINT_INDEX] = input('Programaker bridge endpoint: ')
        if not config[BRIDGE_ENDPOINT_INDEX]:
            raise Exception('No bridge endpoint introduced')
        _save_config(config)
    return config[BRIDGE_ENDPOINT_INDEX]


def get_maintainer_telegram_handle():
    return os.getenv(MAINTAINER_TELEGRAM_HANDLE_ENV, DEFAULT_MAINTAINER_TELEGRAM_HANDLE)


def get_auth_token():
    env_val = os.getenv(AUTH_TOKEN_ENV, None)
    if env_val is not None:
        return env_val

    config = _get_config()
    if config.get(AUTH_TOKEN_INDEX, None) is None:
        config[AUTH_TOKEN_INDEX] = input('Programaker authentication TOKEN: ')
        if not config[AUTH_TOKEN_INDEX]:
            raise Exception('No authentication token introduced')
        _save_config(config)
    return config[AUTH_TOKEN_INDEX]
