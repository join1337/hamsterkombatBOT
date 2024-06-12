from pyrogram import Client

from bot.config import settings
from bot.utils import logger


async def register_sessions() -> None:
    API_ID = settings.API_ID
    API_HASH = settings.API_HASH

    if not API_ID or not API_HASH:
        raise ValueError("API_ID и API_HASH не найдены в файле .env")

    session_name = input('\nназвание сессии (enter чтобы выйти): ')

    if not session_name:
        return None

    session = Client(
        name=session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir="sessions/"
    )

    async with session:
        user_data = await session.get_me()

    logger.success(f'сессия @{user_data.username} успешно добавлена | {user_data.first_name} {user_data.last_name}')
