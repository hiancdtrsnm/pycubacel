#!/usr/bin/python

import json
import requests
from parsel import Selector
import gi
from gi.repository import Gio
import maya
from datetime import date, timedelta
import typer
from pathlib import Path
import datetime
import pgrep
import os

LOGIN_URL = 'https://mi.cubacel.net:8443/login/Login'
BASE_HOST = 'https://mi.cubacel.net'

# LOGIN_URL = 'https://152.206.129.20:8443/login/Login'
# BASE_HOST = 'https://152.206.129.20'


def to_MB(cant, unit):
    if unit == 'GB':
        return float(cant) * 1024

    return float(cant)


def get_quota(login_data):
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

    print(links)

    resp = session.get(f'{BASE_HOST}{links["My Account"]}')

    sel = Selector(text=resp.text)

    cant = sel.xpath('//*[@id="myStat_3001"]/@data-text').get()
    unidad = sel.xpath('//*[@id="myStat_3001"]/@data-info').get()

    cant_lte = sel.xpath('//*[@id="myStat_30012"]/@data-text').get()
    unidad_lte = sel.xpath('//*[@id="myStat_30012"]/@data-info').get()

    days = sel.xpath(
        '//*[@id="multiAccordion"]/div/div[2]/div[1]/div[1]/text()').get()


    maya_time = maya.parse(str(date.today() + timedelta(days=int(days))))

    gi.require_version('Gio', '2.0')
    Application = Gio.Application.new(
        "hello.world", Gio.ApplicationFlags.FLAGS_NONE)
    Application.register()
    Notification = Gio.Notification.new(
        f"Pycubacel (finish {maya_time.slang_time()})")
    Notification.set_body(
        f"La cuenta vence en: {days} días\n\nQuedan: {cant_lte}{unidad_lte} de bono LTE\nQuedan: {cant}{unidad} de Internet")
    Icon = Gio.ThemedIcon.new("dialog-information")
    Notification.set_icon(Icon)
    Application.send_notification(None, Notification)

    print(
        f"La cuenta vence en: {days} días\n\nQuedan: {cant_lte}{unidad_lte} de bono LTE\nQuedan: {cant}{unidad} de Internet")

    return {
        'lte': {
            'cant': to_MB(cant_lte, unidad_lte)
        },
        'normal': {
            'cant': to_MB(cant, unidad)
        }
    }


def main(config_path: Path):
    FORM_DATA = json.load(config_path.open())
    ans = {}
    start = datetime.datetime.now()
    internet = get_quota(FORM_DATA["login"])
    ans['internet'] = internet
    ans['duration'] = datetime.datetime.now() - start
    ans['timestamp'] = datetime.datetime.now()
    ans['openvpn'] = pgrep.pgrep('openvpn')
    ans['user'] = FORM_DATA['login']['username']
    try:
        open(os.path.expanduser(FORM_DATA['data_path']), 'a').write(json.dumps(ans, default=str, ensure_ascii=False) + '\n')

    except Exception as e:
        print(e)
    return ans


if __name__ == "__main__":
    typer.run(main)
