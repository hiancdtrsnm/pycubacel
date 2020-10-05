import re
import time
from typing import Dict, Any
from requests import Session
from .costants import cookie_template as my_cookie

_phone_validator = re.compile('5[0-9]{7}$')

def validate_phone(phone):
    return True if _phone_validator.match(phone) else False

def dump_cookies(cookieJar):
    cookies = []
    for cookie in cookieJar:
        cookied = {i:getattr(cookie, i) for i in my_cookie.keys()}
        cookies.append(cookied)
    return cookies

def load_cookies(session: Session, cookies: Dict[str, Any]):
    for cookie in cookies:
        data = {}
        expired = False
        for i in my_cookie.keys():
            if i in cookie:
                if i == 'expires' and cookie[i] is not None:
                    expired = cookie[i] <= time.time()
                data[i] = cookie[i]
        if not expired:
            session.cookies.set(**data)
    return session.cookies.get('portaluser') is not None

def bound_float(n):
    if n <= 1e-16 or float("%.3f" % n) <= 1e-16:
        return "0"
    return "%.3f" % n

def to_MB(cant, unit):
    if unit == 'GB':
        return bound_float(float(cant) * 1024)
    if unit == 'KB':
        return bound_float(float(cant)/1024)
    if unit == 'B':
        return bound_float(float(cant)/(1024**2))
    return bound_float(float(cant))
