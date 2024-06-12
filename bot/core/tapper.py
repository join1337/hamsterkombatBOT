import asyncio
import json
import operator
from time import time
from random import randint
from urllib.parse import unquote

import aiohttp

from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView
from pyrogram.raw.types.input_peer_user import InputPeerUser 
from pyrogram.raw.types.input_peer_user_from_message import InputPeerUserFromMessage
# from pyrogram.raw.all import 

from bot.config import settings
from bot.utils import logger
from bot.utils.scripts import get_auth_key, save_auth_key
from bot.exceptions import InvalidSession
from bot.utils.fingerprint import FINGERPRINT
from bot.utils.scripts import escape_html, decode_cipher, get_headers

class Tapper:
    def __init__(self, tg_client: Client):
        self.upgrade_cooldowns = {}
        self.session_name = tg_client.name
        self.tg_client = tg_client

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        tg_web_data = get_auth_key(self.tg_client.name)
        if not tg_web_data:
            try:
                if not self.tg_client.is_connected:
                    try:
                        await self.tg_client.connect()
                    except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                        raise InvalidSession(self.session_name)
                dialogs = self.tg_client.get_dialogs()
                async for dialog in dialogs:
                    if dialog.chat and dialog.chat.username and dialog.chat.username == 'hamster_kombat_bot':
                        break

                while True:
                    try:
                        peer = await self.tg_client.resolve_peer('hamster_kombat_bot')
                        break
                    except FloodWait as fl:
                        fls = fl.value

                        logger.warning(f"{self.session_name} | FloodWait {fl}")
                        fls *= 2
                        logger.info(f"{self.session_name} | Sleep {fls}s")

                        await asyncio.sleep(fls)
                web_view = await self.tg_client.invoke(RequestWebView(
                    peer=peer,
                    bot=peer,
                    platform='android',
                    from_bot_menu=False,
                    url='https://hamsterkombat.io/'
                ))

                auth_url = web_view.url
                tg_web_data = unquote(
                    string=unquote(
                        string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))

                save_auth_key(self.tg_client.name, tg_web_data)

                if self.tg_client.is_connected:
                    await self.tg_client.disconnect()

            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error during Authorization: {error.with_traceback(None)}")
                await asyncio.sleep(delay=3)

        return tg_web_data

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str) -> str:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/auth/auth-by-telegram-webapp',
                                              json={"initDataRaw": tg_web_data, "fingerprint": FINGERPRINT})
            response_text = await response.text()
            response.raise_for_status()

            response_json = await response.json()
            access_token = response_json['authToken']

            return access_token
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Access Token: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)

    async def get_profile_data(self, http_client: aiohttp.ClientSession) -> dict[str]:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/sync',
                                              json={})
            response_text = await response.text()
            if response.status != 422:
                response.raise_for_status()

            response_json = json.loads(response_text)
            profile_data = response_json.get('clickerUser', None) or response_json.get("found", {}).get("clickerUser", {})

            return profile_data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Profile Data: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)

    async def get_config(self, http_client: aiohttp.ClientSession) -> dict[str]:
        response_text = ''
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/config',
                                              json={})
            response_text = await response.text()
            response.raise_for_status()

            response_json = await response.json()
            config = response_json

            return config
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Config: {error} | "
                         f"Response text: {escape_html(response_text)[:256]}...")
            await asyncio.sleep(delay=3)

    async def get_tasks(self, http_client: aiohttp.ClientSession) -> dict[str]:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/list-tasks',
                                              json={})
            response_text = await response.text()
            response.raise_for_status()

            response_json = await response.json()
            tasks = response_json['tasks']

            return tasks
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Tasks: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)

    async def select_exchange(self, http_client: aiohttp.ClientSession, exchange_id: str) -> bool:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/select-exchange',
                                              json={'exchangeId': exchange_id})
            response_text = await response.text()
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while Select Exchange: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)

            return False

    async def get_daily(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/check-task',
                                              json={'taskId': "streak_days"})
            response_text = await response.text()
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Daily: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)

            return False

    async def apply_boost(self, http_client: aiohttp.ClientSession, boost_id: str) -> bool:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/buy-boost',
                                              json={'timestamp': time(), 'boostId': boost_id})
            response_text = await response.text()
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while Apply {boost_id} Boost: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)

            return False

    async def get_upgrades(self, http_client: aiohttp.ClientSession) -> list[dict]:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/upgrades-for-buy',
                                              json={})
            response_text = await response.text()
            response.raise_for_status()

            response_json = await response.json()
            upgrades = response_json['upgradesForBuy']

            return upgrades
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Upgrades: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)

    async def buy_upgrade(self, http_client: aiohttp.ClientSession, upgrade_id: str) -> bool:
        if self.upgrade_cooldowns.get(upgrade_id, 0) > time():

            return False
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/buy-upgrade',
                                              json={'timestamp': time(), 'upgradeId': upgrade_id})
            response_text = await response.text()
            if response.status == 400:
                response_json = json.loads(response_text)
                if response_json["error_code"] == "UPGRADE_COOLDOWN":
                    # self.upgrade_cooldown = time() + 5 + response_json["cooldownSeconds"]
                    self.upgrade_cooldowns[upgrade_id] = time() + response_json["cooldownSeconds"] + 5
                    logger.info(f"{self.session_name: <8} | Upgrade <e>{upgrade_id}</e> | Wait {round(self.upgrade_cooldowns[upgrade_id] - time())}сек.")
                    return False
            if response.status != 422:
                response.raise_for_status()

            response_json = json.loads(response_text)
            profile_data = response_json.get('clickerUser', None) or response_json.get("found", {}).get("clickerUser", {})


            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while buying Upgrade: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)

            return False

    async def get_boosts(self, http_client: aiohttp.ClientSession) -> list[dict]:
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/boosts-for-buy', json={})
            response_text = await response.text()
            response.raise_for_status()

            response_json = await response.json()
            boosts = response_json['boostsForBuy']

            return boosts
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Boosts: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)
        
    async def claim_daily_cipher(self, http_client: aiohttp.ClientSession, cipher: str) -> bool:
        response_text = ''
        try:
            response = await http_client.post(url='https://api.hamsterkombat.io/clicker/claim-daily-cipher',
                                              json={'cipher': cipher})
            response_text = await response.text()
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while Claim Daily Cipher: {error} | "
                         f"Response text: {escape_html(response_text)[:256]}...")
            await asyncio.sleep(delay=3)

            return False

    async def send_taps(self, http_client: aiohttp.ClientSession, available_energy: int, taps: int) -> dict[str]:
        try:
            response = await http_client.post(
                url='https://api.hamsterkombat.io/clicker/tap',
                json={'availableTaps': available_energy, 'count': taps, 'timestamp': time()})
            response_text = await response.text()
            if response.status != 422:
                response.raise_for_status()

            response_json = json.loads(response_text)
            player_data = response_json.get('clickerUser', None) or response_json.get("found", {}).get("clickerUser", {})


            return player_data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while Tapping: {error} | "
                         f"Response text: {escape_html(response_text)}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        turbo_time = 0
        active_turbo = False

        headers = get_headers(name=self.tg_client.name)

        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        http_client = aiohttp.ClientSession(
            headers=headers, connector=proxy_conn
        )

        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            if proxy:
                await self.check_proxy(http_client=http_client, proxy=proxy)

            tg_web_data = await self.get_tg_web_data(proxy=proxy)

            while True:
                try:
                    if time() - access_token_created_time >= 3600:
                        access_token = await self.login(http_client=http_client, tg_web_data=tg_web_data)

                        if not access_token:
                            continue

                        http_client.headers[
                            'Authorization'
                        ] = f'Bearer {access_token}'

                        access_token_created_time = time()

                        game_config = await self.get_config(http_client=http_client)
                        profile_data = await self.get_profile_data(http_client=http_client)

                        if not profile_data:
                            continue

                        exchange_id = profile_data.get('exchangeId')
                        if not exchange_id:
                            status = await self.select_exchange(http_client=http_client, exchange_id="bybit")
                            if status is True:
                                logger.success(f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour}</y><g>/ч</g> | Баланс:  <c>{balance}</c> | Успешно получена дневная награда! | ")

                        last_passive_earn = profile_data['lastPassiveEarn']
                        earn_on_hour = profile_data['earnPassivePerHour']

                        logger.info(f"{self.session_name: <8} | Последний пассивный доход: <g>+Money: {last_passive_earn}</g> | "
                                    f"<y>{earn_on_hour}</y><r>/ч</r>")

                        available_energy = profile_data.get('availableTaps', 0)
                        balance = int(profile_data['balanceCoins'])

                        tasks = await self.get_tasks(http_client=http_client)

                        daily_task = tasks[-1]
                        rewards = daily_task['rewardsByDays']
                        is_completed = daily_task['isCompleted']
                        days = daily_task['days']

                        if is_completed is False:
                            status = await self.get_daily(http_client=http_client)
                            if status is True:
                                if status is True:
                                    logger.success(
                                        f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour}</y><g>/ч</g> | Баланс: <c>{balance}</c> | Успешно получена дневная награда! | "
                                        f"День: <m>{days}</m> | 💵 {rewards[days - 1]['rewardCoins']}"
    )


                    taps = randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])

                    if active_turbo:
                        taps += settings.ADD_TAPS_ON_TURBO
                        if time() - turbo_time > 20:
                            active_turbo = False
                            turbo_time = 0
                    if not "available_energy" in locals():
                        logger.error(f"{self.session_name: <8} | Обнаружен неудачный вход в систему, дальнейшее продолжение невозможно. Вы вышли из системы со всех своих устройств? Пожалуйста, скинь свои логи сюда https://github.com/shamhi/HamsterKombatBot/pull/72.")
                        input("Нажми Enter чтобы выйти...")
                        exit(1)
                    player_data = await self.send_taps(http_client=http_client,
                                                       available_energy=available_energy,
                                                       taps=taps)

                    daily_cipher = game_config.get('dailyCipher')
                    if daily_cipher:
                        cipher = daily_cipher['cipher']
                        bonus = daily_cipher['bonusCoins']
                        is_claimed = daily_cipher['isClaimed']

                        if not is_claimed and cipher:
                            decoded_cipher = decode_cipher(cipher=cipher)

                            status = await self.claim_daily_cipher(http_client=http_client, cipher=decoded_cipher)
                            if status is True:
                                logger.success(f"{self.session_name} | "
                                               f"Successfully claim daily cipher: <y>{decoded_cipher}</y> | "
                                               f"Bonus: <g>+{bonus:,}</g>")

                        await asyncio.sleep(delay=2)

                    if not player_data:
                        continue

                    available_energy = player_data.get('availableTaps', 0)
                    new_balance = int(player_data.get('balanceCoins', 0))
                    calc_taps = new_balance - balance
                    balance = new_balance
                    total = int(player_data.get('totalCoins', 0))
                    earn_on_hour = player_data.get('earnPassivePerHour',0)
                    MAX_EARN_FOR_UPGRADE_HOURS = settings.MAX_EARN_FOR_UPGRADE_HOURS
                    TIME_TO_WAIT_BEFORE_UPGRADE = settings.WAIT_SECONDS_BEFORE_UPGRADE
                    PLAYER_DATA_TAPS_RECOVER_PER_SEC = player_data.get('tapsRecoverPerSec', 0)
                    PLAYER_DATA_EARN_PASSIVE_PER_HOUR = player_data.get('earnPassivePerHour', 0)
                    PLAYER_DATA_HOURLY_EARNINGS = 3600 * PLAYER_DATA_TAPS_RECOVER_PER_SEC + PLAYER_DATA_EARN_PASSIVE_PER_HOUR

                    boosts = await self.get_boosts(http_client=http_client)
                    energy_boost = next((boost for boost in boosts if boost['id'] == 'BoostFullAvailableTaps'), {})

                    logger.success(f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час <y>{earn_on_hour:,}</y><r>/ч</r> | Баланс <c>{balance}</c>")

                    if active_turbo is False:
                        if (settings.APPLY_DAILY_ENERGY is True
                                and available_energy <= settings.MIN_AVAILABLE_ENERGY
                                and energy_boost.get("cooldownSeconds", 0) == 0
                                and energy_boost.get("level", 0) <= energy_boost.get("maxLevel", 0)):
                            logger.info(f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour:,}</y><r>/ч</r> | Всего денег: <c>{balance:,}</c> | <y>5</y> сек. | Activation Boost")
                            await asyncio.sleep(delay=5)

                            status = await self.apply_boost(http_client=http_client, boost_id="BoostFullAvailableTaps")
                            if status is True:
                                logger.success(f"{self.session_name: <8} Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour:,}</y><r>/ч</r> | Всего денег: <c>{balance:,}</c> | Activation Boost")

                                await asyncio.sleep(delay=1)

                                continue

                        if settings.AUTO_UPGRADE is True:
                            upgrades = await self.get_upgrades(http_client=http_client)
                            available_upgrades = [data for data in upgrades if
                                                  data['isAvailable'] is True and data['isExpired'] is False]
                            queue = []

                            for upgrade in available_upgrades:
                                upgrade_id = upgrade['id']
                                level = upgrade['level']
                                price = upgrade['price']
                                profit = upgrade['profitPerHourDelta']

                                significance = profit / max(1, price)

                                if level <= settings.MAX_LEVEL:
                                    queue.append([upgrade_id, significance, level, price, profit])
                            best_upgrade = max(queue, key=lambda x: x[1])
                            
                            time_to_be_earned = (best_upgrade[3] - balance) / PLAYER_DATA_HOURLY_EARNINGS
                            while time_to_be_earned > MAX_EARN_FOR_UPGRADE_HOURS or self.upgrade_cooldowns.get(best_upgrade[0], 0) > time():
                                queue.remove(best_upgrade)
                                best_upgrade = max(queue, key=lambda x: x[1])
                                time_to_be_earned = (best_upgrade[3] - balance) / PLAYER_DATA_HOURLY_EARNINGS

                            logger.info(f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour:,}</y><r>/ч</r> | Всего денег: <c>{balance:,}</c> | Улучшено: <e>{best_upgrade[0]}</e> | Потрачено для улучшения: <y>{best_upgrade[3]}</y> | AFK: <y>{round(time_to_be_earned * 60 if time_to_be_earned > 0 else 0)}</y> мин.")
                            if balance >= best_upgrade[3]:
                        

                                if balance > best_upgrade[3] and best_upgrade[2] <= settings.MAX_LEVEL:
                                    logger.info(f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour:,}</y><r>/ч</r> | Всего денег: <c>{balance:,}</c> | Времени до следующего улучшения: <y>{TIME_TO_WAIT_BEFORE_UPGRADE}</y> сек. | Улучшено: <e>{best_upgrade[0]}</e>")
                                    await asyncio.sleep(delay=TIME_TO_WAIT_BEFORE_UPGRADE)

                                    status = await self.buy_upgrade(http_client=http_client, upgrade_id=best_upgrade[0])

                                    if status is True:
                                        earn_on_hour += best_upgrade[4]
                                        balance -= best_upgrade[3]
                                        logger.success(
                                            f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour:,}</y><r>/ч</r> | Всего денег: <c>{balance:,}</c> | "
                                            f"Upgrade <e>{best_upgrade[0]}</e> | <m>{best_upgrade[2]}</m> lvl | "
                                            f"<g>+{best_upgrade[4]}</g><r>/ч</r>")

                                        await asyncio.sleep(delay=1)

                                continue

                        if available_energy <= settings.MIN_AVAILABLE_ENERGY:
                            logger.info(f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour:,}</y><r>/ч</r> | Всего денег: <c>{balance:,}</c> | Достигнуто минимальное значение энергии<m>{available_energy}</m>")
                            logger.info(f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour:,}</y><r>/ч</r> | Всего денег: <c>{balance:,}</c> | Sleep <y>{settings.SLEEP_BY_MIN_ENERGY}</y> сек.")

                            await asyncio.sleep(delay=settings.SLEEP_BY_MIN_ENERGY)

                            continue

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name: <8} | Неизвестная ошибка {error}")
                    await asyncio.sleep(delay=3)

                else:
                    sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])

                    if active_turbo is True:
                        sleep_between_clicks = 4

                    logger.info(f"{self.session_name: <8} | Общее количество: <e>{total:,}</e> | Заработок в час: <y>{earn_on_hour:,}</y><r>/ч</r> | Всего денег: <c>{balance:,}</c> | Sleep <y>{sleep_between_clicks}</y> сек.")
                    await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Недействительная сессия")
