#!/usr/bin/python

import json
import requests
from parsel import Selector
from datetime import date, timedelta
import typer
from pathlib import Path
import datetime
import pgrep
import os
import urllib3
import psutil

OPENVPN_PROCCESS_NAME = "openvpn"

LOGIN_URL = 'https://mi.cubacel.net:8443/login/Login'
BASE_HOST = 'https://mi.cubacel.net'

# LOGIN_URL = 'https://152.206.129.20:8443/login/Login'
# BASE_HOST = 'https://152.206.129.20'


def to_MB(cant, unit):
    if unit == 'GB':
        return float(cant) * 1024

    return float(cant)


def get_quota(login_data):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    session = requests.Session()

    resp = session.post(LOGIN_URL, data=login_data, verify=False)

    sel = Selector(text=resp.text)

    url = sel.xpath('//*[@id="englishLanguage"]/@href').get()

    resp = session.get(f'{BASE_HOST}{url}')

    sel = Selector(text=resp.text)

    links = sel.xpath(
        '//*[@class="module_"]/div/div/div/div/div[2]/nav/div/div/ul/li/a/@href').getall()[:-1]
    names = sel.xpath(
        '//*[@class="module_"]/div/div/div/div/div[2]/nav/div/div/ul/li/a/text()').getall()[:-1]

    links = {name.strip(): link for name, link in zip(names, links)}

    resp = session.get(f'{BASE_HOST}{links["My Account"]}')

    sel = Selector(text=resp.text)

    cant = sel.xpath('//*[@id="myStat_3001"]/@data-text').get()
    unidad = sel.xpath('//*[@id="myStat_3001"]/@data-info').get()

    cant_lte = sel.xpath('//*[@id="myStat_30012"]/@data-text').get()
    unidad_lte = sel.xpath('//*[@id="myStat_30012"]/@data-info').get()

    days = sel.xpath(
        '//*[@id="multiAccordion"]/div/div[2]/div[1]/div[1]/text()').get()

    only_lte = sel.xpath('//*[@id="multiAccordion"]/div/div[1]/div[1]/div[2]/text()').get()

    container_account_details_selector = sel.xpath('//*[@id="service_663ba72d-fe96-427f-880f-9998215775dd"]/div/div[3]/div[1]')

    credit = container_account_details_selector.xpath('./div[1]/div[1]/div[2]/span[2]/span/text()').get()
    credit_expire_date = container_account_details_selector.xpath('./div[1]/div[2]/div[2]/span[2]/text()').get()

    bonus_credit = container_account_details_selector.xpath('./div[3]/div[1]/div[2]/span[2]/text()').get()
    bonus_credit_expire_date = container_account_details_selector.xpath('./div[3]/div[2]/div[1]/span[2]/text()').get()

    national_data = container_account_details_selector.xpath('./div[5]/div[1]')
    national_data_value = sel.xpath('//*[@id="myStat_bonusDataN"]/@data-text').get()
    national_data_unit = sel.xpath('//*[@id="myStat_bonusDataN"]/@data-info').get()
    national_data_value = to_MB(national_data_value, national_data_unit)

    only_lte = only_lte.split(':')[1][1:-1]

    print(f"-" * 30)
    print(f"Saldo principal: {credit} vence el {credit_expire_date}")
    print(f"Saldo bono: {bonus_credit} vence el {bonus_credit_expire_date}")
    print(f"-" * 30)
    print(f"Quedan: {cant} {unidad} de Internet")
    print(f"Quedan: {only_lte} de Internet (Solo LTE)")
    print(f"Quedan: {cant_lte} {unidad_lte} de bono LTE")
    print(f"Quedan: {national_data_value} {national_data_unit} de Navegación Nacional\n")
    print(f"La cuenta vence en: {days} días")
    print(f"-" * 30)

    credit_split = credit.split(' ')
    bonus_credit_split = bonus_credit.split(' ')
    only_lte_split = only_lte.split(' ')

    return {
        'lte': {
            'cant': to_MB(cant_lte, unidad_lte),
            'unit': unidad
        },
        'only_lte':{
            'cant' : float(only_lte_split[0]),
            'unit' : only_lte_split[1]
        },
        'normal': {
            'cant': to_MB(cant, unidad),
            'unit': unidad
        },
        'credit': {
            'cant' : float(credit_split[0]),
            'unit' : credit_split[1]
        },
        'credit_bonus':{
            'cant' : float(bonus_credit_split[0]),
            'unit' : bonus_credit_split[1]
        },
        'national_data':{
            'cant' : national_data_value,
            'unit' : national_data_unit
        }
    }


def consult(config_path: Path):
    FORM_DATA = json.load(config_path.open())
    ans = {}
    start = datetime.datetime.now()
    internet = get_quota(FORM_DATA["login"])
    ans['internet'] = internet
    ans['duration'] = datetime.datetime.now() - start
    ans['timestamp'] = datetime.datetime.now()
    ans['openvpn'] = [proc.pid for proc in psutil.process_iter() if OPENVPN_PROCCESS_NAME in proc.name()]
    ans['user'] = FORM_DATA['login']['username']
    
    try:
        open(os.path.expanduser(FORM_DATA['data_path']), 'a').write(json.dumps(ans, default=str, ensure_ascii=False) + '\n')
    except Exception as e:
        print(e)
    return ans


if __name__ == "__main__":
    typer.run(consult)
