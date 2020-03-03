import json
import requests
from parsel import Selector
import gi
from gi.repository import Gio

# https://mi.cubacel.net:8443/AirConnector/rest/AirConnect/getResults?subscriber=5353862908&startDate=27/01/2020&endDate=27/02/2020&origin=0&plans=0

session = requests.Session()

LOGIN_URL = 'https://mi.cubacel.net:8443/login/Login'
BASE_HOST = 'https://mi.cubacel.net'

FORM_DATA = json.load(open('config.json'))

resp = session.post(LOGIN_URL, data=FORM_DATA, verify=False)

sel = Selector(text=resp.text)

url = sel.xpath('//*[@id="englishLanguage"]/@href').get()


resp = session.get(f'{BASE_HOST}{url}')

sel = Selector(text=resp.text)

links = sel.xpath('//*[@class="module_"]/div/div/div/div/div[2]/nav/div/div/ul/li/a/@href').getall()[:-1]
names = sel.xpath('//*[@class="module_"]/div/div/div/div/div[2]/nav/div/div/ul/li/a/text()').getall()[:-1]

links = {name.strip(): link for name, link in zip(names, links)}

print(links)

resp = session.get(f'{BASE_HOST}{links["My Account"]}')


sel = Selector(text=resp.text)

cant = sel.xpath('//*[@id="myStat_3001"]/@data-text').get()
unidad = sel.xpath('//*[@id="myStat_3001"]/@data-info').get()

cant_lte = sel.xpath('//*[@id="myStat_30012"]/@data-text').get()
unidad_lte = sel.xpath('//*[@id="myStat_30012"]/@data-info').get()

days = sel.xpath('//*[@id="multiAccordion"]/div/div[2]/div[1]/div[1]/text()').get()


print(days, cant, cant_lte)


gi.require_version('Gio', '2.0')
Application = Gio.Application.new("hello.world", Gio.ApplicationFlags.FLAGS_NONE)
Application.register()
Notification = Gio.Notification.new(f"Pycubacel ({days})")
Notification.set_body(f"La cuenta vence en: {days}\n\nQuedan: {cant_lte}{unidad_lte} de bono LTE\nQuedan: {cant}{unidad} de Internet")
Icon = Gio.ThemedIcon.new("dialog-information")
Notification.set_icon(Icon)
Application.send_notification(None, Notification)