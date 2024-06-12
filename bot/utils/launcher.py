import os
import re
import glob
import asyncio
import argparse
from itertools import cycle

from pyrogram import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions

from bot import __version__ 

start_text = f"""

 _   _                     _              _   __                _           _     _           _   
| | | |                   | |            | | / /               | |         | |   | |         | |  
| |_| | __ _ _ __ ___  ___| |_ ___ _ __  | |/ /  ___  _ __ ___ | |__   __ _| |_  | |__   ___ | |_ 
|  _  |/ _` | '_ ` _ \/ __| __/ _ \ '__| |    \ / _ \| '_ ` _ \| '_ \ / _` | __| | '_ \ / _ \| __|
| | | | (_| | | | | | \__ \ ||  __/ |    | |\  \ (_) | | | | | | |_) | (_| | |_  | |_) | (_) | |_ 
\_| |_/\__,_|_| |_| |_|___/\__\___|_|    \_| \_/\___/|_| |_| |_|_.__/ \__,_|\__| |_.__/ \___/ \__|
--------------------------------------------------------------------------------------------------
Version: {str(__version__)}
--------------------------------------------------------------------------------------------------

Выберите опцию:

    1. Добавить сессию
    2. Запустить кликер
"""


def get_session_names() -> list[str]:
  session_names = glob.glob('sessions/*.session')
  session_names = [os.path.splitext(os.path.basename(file))[0] for file in session_names]

  return session_names



def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file='bot/config/proxies.txt', encoding='utf-8-sig') as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_tg_clients() -> list[Client]:
    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Не найдены файлы сессий")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID и API_HASH не найдены в .env файле.")

    tg_clients = [Client(
        name=session_name,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        workdir='sessions/',
        plugins=dict(root='bot/plugins')
    ) for session_name in session_names]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--action', type=int, help='Действие для выполнения')

    logger.info(f"Обнаружено {len(get_session_names())} сессий | {len(get_proxies())} прокси")

    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Укажите номер действия")
            elif action not in ['1', '2']:
                logger.warning("Выберите номер 1 или 2")
            else:
                action = int(action)
                break

    if action == 1:
        await register_sessions()
    elif action == 2:
        tg_clients = await get_tg_clients()

        await run_tasks(tg_clients=tg_clients)


async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [asyncio.create_task(run_tapper(tg_client=tg_client, proxy=next(proxies_cycle) if proxies_cycle else None))
             for tg_client in tg_clients]

    await asyncio.gather(*tasks)
