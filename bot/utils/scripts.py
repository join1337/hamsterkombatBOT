import json
import hashlib
import random
import string
import base64

from fake_useragent import UserAgent

from bot.config import settings

def generate_random_visitor_id():
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    visitor_id = hashlib.md5(random_string.encode()).hexdigest()

    return visitor_id


def escape_html(text: str) -> str:
    return text.replace('<', '\\<').replace('>', '\\>')

def decode_cipher(cipher: str) -> str:
    encoded = cipher[:3] + cipher[4:]
    return base64.b64decode(encoded).decode('utf-8')

def get_mobile_user_agent() -> str:
    """
    Function: get_mobile_user_agent

    This method generates a random mobile user agent for an Android platform.
    If the generated user agent does not contain the "wv" string,
    it adds it to the browser version component.

    :return: A random mobile user agent for Android platform.
    """
    ua = UserAgent(platforms=['mobile'], os=['android'])
    user_agent = ua.random
    if 'wv' not in user_agent:
        parts = user_agent.split(')')
        parts[0] += '; wv'
        user_agent = ')'.join(parts)
    return user_agent


def get_headers(name: str):
    try:
        with open('profile.json', 'r') as file:
            profile = json.load(file)
    except:
        profile = {}

    headers = profile.get(name, {}).get('headers', {})

    if settings.USE_RANDOM_USERAGENT:
        android_version = random.randint(24, 33)
        webview_version = random.randint(70, 125)

        headers['Sec-Ch-Ua'] = (
            f'"Android WebView";v="{webview_version}", '
            f'"Chromium";v="{webview_version}", '
            f'"Not?A_Brand";v="{android_version}"'
        )
        headers['User-Agent'] = get_mobile_user_agent()

    return headers

def get_auth_key(session_name: str) -> str | None:
    try:
        with open('auth_keys.json', 'r', encoding="utf-8") as file:
            auth_keys = json.load(file)

        auth_key = auth_keys.get(session_name)
        return auth_key
    except FileNotFoundError:
        return None


def save_auth_key(session_name: str, auth_key: str) -> None:
    try:
        with open('auth_keys.json', 'r', encoding="utf-8") as file:
            auth_keys = json.load(file)
    except FileNotFoundError:
        auth_keys = {}

    auth_keys[session_name] = auth_key
    with open('auth_keys.json', 'w', encoding="utf-8") as file:
        json.dump(auth_keys, file, indent=4, ensure_ascii=False)
import json
import hashlib
import random
import string
import base64

from fake_useragent import UserAgent

from bot.config import settings

def generate_random_visitor_id():
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    visitor_id = hashlib.md5(random_string.encode()).hexdigest()

    return visitor_id


def escape_html(text: str) -> str:
    return text.replace('<', '\\<').replace('>', '\\>')

def decode_cipher(cipher: str) -> str:
    encoded = cipher[:3] + cipher[4:]
    return base64.b64decode(encoded).decode('utf-8')

def get_mobile_user_agent() -> str:
    """
    Function: get_mobile_user_agent

    This method generates a random mobile user agent for an Android platform.
    If the generated user agent does not contain the "wv" string,
    it adds it to the browser version component.

    :return: A random mobile user agent for Android platform.
    """
    ua = UserAgent(platforms=['mobile'], os=['android'])
    user_agent = ua.random
    if 'wv' not in user_agent:
        parts = user_agent.split(')')
        parts[0] += '; wv'
        user_agent = ')'.join(parts)
    return user_agent


def get_headers(name: str):
    try:
        with open('profile.json', 'r') as file:
            profile = json.load(file)
    except:
        profile = {}

    headers = profile.get(name, {}).get('headers', {})

    if settings.USE_RANDOM_USERAGENT:
        android_version = random.randint(24, 33)
        webview_version = random.randint(70, 125)

        headers['Sec-Ch-Ua'] = (
            f'"Android WebView";v="{webview_version}", '
            f'"Chromium";v="{webview_version}", '
            f'"Not?A_Brand";v="{android_version}"'
        )
        headers['User-Agent'] = get_mobile_user_agent()

    return headers

def get_auth_key(session_name: str) -> str | None:
    try:
        with open('auth_keys.json', 'r', encoding="utf-8") as file:
            auth_keys = json.load(file)

        auth_key = auth_keys.get(session_name)
        return auth_key
    except FileNotFoundError:
        return None


def save_auth_key(session_name: str, auth_key: str) -> None:
    try:
        with open('auth_keys.json', 'r', encoding="utf-8") as file:
            auth_keys = json.load(file)
    except FileNotFoundError:
        auth_keys = {}

    auth_keys[session_name] = auth_key
    with open('auth_keys.json', 'w', encoding="utf-8") as file:
        json.dump(auth_keys, file, indent=4, ensure_ascii=False)
