#! /bin/env python

import os
import json
import time
import datetime
import logging
import warnings
from pathlib import Path
from urllib3.connectionpool import InsecureRequestWarning
import requests
from parsel import Selector
import typer

warnings.filterwarnings('ignore', category=InsecureRequestWarning)

logging.basicConfig(level=logging.DEBUG)

my_cookie = {
    "version": 0,
    "name": 'COOKIE_NAME',
    "value": 'true',
    "port": None,
    # "port_specified":False,
    "domain": 'www.mydomain.com',
    # "domain_specified":False,
    # "domain_initial_dot":False,
    "path": '/',
    # "path_specified":True,
    "secure": False,
    "expires": None,
    "discard": True,
    "comment": None,
    "comment_url": None,
    "rfc2109": False
}

user_agent = 'Mozilla/5.0 (Linux; Android 9.0; MI 8 SE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.119 Mobile Safari/537.36'
url_base = 'https://mi.cubacel.net'
url_login = 'https://mi.cubacel.net:8443/login/Login'

class BadCredentials(Exception): pass

def to_MB(cant, unit):
    if unit == 'GB':
        return float(cant) * 1024

    return float(cant)

def get_data(page, Id):
    bono = page.css(f'div#{Id}')[0]
    bono_data = {'value':'', 'scale':''}
    bono_data['value']=bono.attrib.get('data-text','0').strip()
    bono_data['scale']=bono.attrib.get('data-info','0').strip()
    # TODO: extraer si son dias u horas, por ahora se asume siempre dias
    day = bono.xpath('parent::div').xpath('parent::div').xpath('parent::div').css('.expires_date::text').get().strip()
    bono_data['days'] = day
    return bono_data

def get_national_bonus(page):
    bono_id='myStat_bonusDataN'
    return get_data(page, bono_id)

def get_lte_bonus(page):
    bono_id='myStat_30012'
    return get_data(page, bono_id)

def get_internet(page):
    bono_id='myStat_3001'
    data = get_data(page, bono_id)
    bono = page.css(f'div#{bono_id}')
    parent = bono.xpath('parent::div')
    lte = parent.css('div.network_all::text').get().strip().split()
    alln = parent.css('div.network_all_cero::text').get().strip().split()
    data['only_lte'] = {'value': lte[0], 'scale': lte[1]}
    data['all_networks'] = {'value': alln[0], 'scale': alln[1]}
    return data

def get_min_bonus(page):
    bono_id='myStat_bonusVOZI'
    return get_data(page, bono_id)

def get_sms_bonus(page):
    bono_id='myStat_bonusSMSI'
    return get_data(page, bono_id)

def get_money(page):
    return page.css('span.mbcHlightValue_msdp::text').get().strip()
    #return page.find('span',attrs={'class':'mbcHlightValue_msdp'}).text

def get_bonus_money(page):
    r = page.css('div.myaccount_details_block')
    r=r[-1]
    r=r.css('span.cvalue::text').get().strip()
    return r

def dump_cookies(cookieJar):
    cookies = []
    for cookie in cookieJar:
        cookied = {i:getattr(cookie,i) for i in my_cookie.keys()}
        cookies.append(cookied)
    return cookies

def load_cookies(session, cookies):
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

def get_page(login_data=None, cookies=None, return_if_expired_cookies=False):

    ss = requests.Session()
    ss.headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': user_agent,
    }
    ss.verify=False
    load_ok = load_cookies(ss, cookies)
    if not load_ok:
        res = ss.post(url_login, data=login_data, verify=False)
        sel = Selector(text=res.text)
        if len(sel.css('.error_Block')):
            raise BadCredentials()
    resp = ss.get(url_base).text
    sel = Selector(text=resp)
    url = sel.xpath('//*[@id="englishLanguage"]/@href').get()
    resp = ss.get(f'{url_base}{url}')
    sel = Selector(text=resp.text)
    links = sel.xpath(
        '//*[@class="module_"]/div/div/div/div/div[2]/nav/div/div/ul/li/a/@href').getall()[:-1]
    names = sel.xpath(
        '//*[@class="module_"]/div/div/div/div/div[2]/nav/div/div/ul/li/a/text()').getall()[:-1]
    links = {name.strip(): link for name, link in zip(names, links)}
    cookies = dump_cookies(ss.cookies)
    resp = ss.get(f'{url_base}{links["My Account"]}')
    page=Selector(text=resp.text)
    if return_if_expired_cookies:
        return page, cookies, not load_ok
    return page, cookies

def print_data(page):
    r = get_money(page)
    print("Credit:", r)
    r = get_bonus_money(page)
    print("Credit Bonus:", r)
    r = get_min_bonus(page)
    print("Minute Bonus:", r['value'], r['scale'], 'expire', r['days'])
    r = get_sms_bonus(page)
    print("SMS Bonus:", r['value'] ,r['scale'], 'expire', r['days'])
    r = get_internet(page)
    print("Internet, expire", r['days'],':')
    print('  LTE only:', to_MB(r['only_lte']['value'], r['only_lte']['scale']), 'MB')
    print('  All networks:', to_MB(r['all_networks']['value'], r['all_networks']['scale']), 'MB')
    r = get_lte_bonus(page)
    print("LTE Bonus:", to_MB(r['value'],r['scale']), 'MB expire', r['days'])
    r = get_national_bonus(page)
    print("National Bonus:", r['value'], r['scale'], 'expire', r['days'])

def get_info(page):
    res = {
            'data':{
                'unit' : 'MB',
                'values':{}
            },
            'credit':{
                'unit' : 'CUC',
                'values':{}
            },
            'others':{
                'unit' : None, # for use the same interface, but every data must have his own unit defined inside
                'values':{}
            }
        }
    r = get_internet(page)
    res['data']['values']['normal']={}
    res['data']['values']['normal']['cant'] = to_MB(r['value'],r['scale'])
    res['data']['values']['normal']['expire'] = r['days']
    res['data']['values']['only_lte']={}
    res['data']['values']['only_lte']['cant'] = to_MB(r['only_lte']['value'],r['only_lte']['scale'])
    res['data']['values']['only_lte']['expire'] = r['days']
    res['data']['values']['all_networks']={}
    res['data']['values']['all_networks']['cant'] = to_MB(r['all_networks']['value'],r['all_networks']['scale'])
    res['data']['values']['all_networks']['expire'] = r['days']
    r = get_lte_bonus(page)
    res['data']['values']['lte'] = {}
    res['data']['values']['lte']['cant'] = to_MB(r['value'],r['scale'])
    res['data']['values']['lte']['expire'] = r['days']
    r = get_national_bonus(page)
    res['data']['values']['national_data'] = {}
    res['data']['values']['national_data']['cant'] = to_MB(r['value'],r['scale'])
    res['data']['values']['national_data']['expire'] = r['days']
    r = get_money(page).split(' ')[0].strip()
    res['credit']['values']['credit_normal'] = {}
    res['credit']['values']['credit_normal']['cant'] = r
    r = get_bonus_money(page).split(' ')[0].strip()
    res['credit']['values']['credit_bonus'] = {}
    res['credit']['values']['credit_bonus']['cant'] = r
    r =  get_sms_bonus(page)
    res['others']['values']['sms'] = {}
    res['others']['values']['sms']['cant'] = r['value']
    res['others']['values']['sms']['unit'] = r['scale']
    r =  get_min_bonus(page)
    res['others']['values']['minutes'] = {}
    res['others']['values']['minutes']['cant'] = r['value']
    res['others']['values']['minutes']['unit'] = r['scale']
    return res



def consult(config_path: Path):
    config = json.load(config_path.open())
    cookies_path = os.path.expandvars(os.path.expanduser(config['cookies_path']))
    cookies_path = cookies_path+'.'+config['login']['username']
    if os.path.exists(cookies_path):
        cookies = json.load(open(cookies_path))
    else:
        cookies = {}
    FORM_DATA = config['login']
    page, cookies, expired = get_page(login_data=FORM_DATA, cookies=cookies, return_if_expired_cookies=True)
    if expired:
        json.dump(cookies,open(cookies_path,'w'),indent=2)

    ans = {}
    start = datetime.datetime.now()
    internet = get_info(page)
    ans['internet'] = internet
    ans['duration'] = str(datetime.datetime.now() - start)
    ans['timestamp'] = str(datetime.datetime.now())
    ans['user'] = FORM_DATA['username']
    #TODO: reescribir print_data para no tener q parsear todo denuevo
    print_data(page)
    try:
        open(os.path.expanduser(config['data_path']), 'a').write(json.dumps(ans, default=str, ensure_ascii=False) + '\n')
    except Exception as e:
        print(e)
    return ans


def consult_get(config_path: Path):
    config = json.load(config_path.open())
    cookies_path = os.path.expandvars(os.path.expanduser(config['cookies_path']))
    cookies_path = cookies_path+'.'+config['login']['username']
    if os.path.exists(cookies_path):
        cookies = json.load(open(cookies_path))
    else:
        cookies = {}
    FORM_DATA = config['login']
    page, cookies, expired = get_page(login_data=FORM_DATA, cookies=cookies, return_if_expired_cookies=True)
    if expired:
        json.dump(cookies,open(cookies_path,'w'),indent=2)
    return get_info(page)

if __name__ == "__main__":
    #typer.run(consult)
    consult(Path('config.json'))
