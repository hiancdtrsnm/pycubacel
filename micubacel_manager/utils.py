import time
from typing import Dict, Any
from requests import Session
from .costants import cookie_template as my_cookie

def dump_cookies(cookieJar):
    cookies = []
    for cookie in cookieJar:
        cookied = {i:getattr(cookie,i) for i in my_cookie.keys()}
        cookies.append(cookied)
    return cookies

def load_cookies(session: Session, cookies: Dict[str, Any]):
    for cookie in cookies:
        data = {}
        expired = False
        for i in my_cookie.keys():
            if i in cookie:
                if i=='expires' and cookie[i] is not None:
                    expired = cookie[i] <= time.time()
                data[i] = cookie[i]
        if not expired:
            session.cookies.set(**data)
    return session.cookies.get('portaluser') is not None

def to_MB(cant, unit):
    if unit == 'GB':
        return float(cant) * 1024
    return float(cant)
