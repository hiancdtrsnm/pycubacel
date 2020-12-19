import time
from urllib3.connectionpool import InsecureRequestWarning
import requests
from parsel import Selector
from .costants import HEADERS
from .utils import to_MB

class MiCubacelParser:
    url_base = 'https://mi.cubacel.net'

    def __init__(self, page: str):
        self._sel = Selector(page)
        self._result = None

    @property
    def data(self):
        if self._result is None:
            self.get_data()
        return self._result

    @staticmethod
    def page_ok(page: str):
        sel = Selector(text=page)
        if len(sel.css('.error_Block')):
            return False
        return True

    @staticmethod
    def home_ok(page: str):
        sel = Selector(text=page)
        if len(sel.css('#mySignin')):
            return True
        return False

    @staticmethod
    def lang_url(page: str):
        sel = Selector(text=page)
        url = sel.xpath('//*[@id="englishLanguage"]/@href').get()
        return f'{MiCubacelParser.url_base}{url}'

    @staticmethod
    def my_account(page: str):
        sel = Selector(text=page)
        links = sel.xpath(
            '//*[@class="module_"]/div/div/div/div/div[2]/nav/div/div/ul/li/a/@href').getall()[:-1]
        names = sel.xpath(
            '//*[@class="module_"]/div/div/div/div/div[2]/nav/div/div/ul/li/a/text()').getall()[:-1]
        links = {name.strip(): link for name, link in zip(names, links)}
        return f'{MiCubacelParser.url_base}{links["My Account"]}'

    @staticmethod
    def _parse_data(page: Selector, Id: str):
        bono = page.css(f'div#{Id}')[0]
        bono_data = {'value':'', 'scale':''}
        bono_data['value'] = bono.attrib.get('data-text', '0').strip()
        bono_data['scale'] = bono.attrib.get('data-info', '0').strip()
        # TODO: extraer si son dias u horas, por ahora se asume siempre dias
        day = bono.xpath('parent::div').xpath('parent::div').xpath('parent::div').css('.expires_date::text').get().strip()
        bono_data['days'] = day
        return bono_data

    @staticmethod
    def _default_data():
        return {
            'value': 0,
            'scale': None,
            'days': 0,
        }

    @staticmethod
    def _get_national_bonus(page: Selector):
        bono_id = 'myStat_bonusDataN'
        try:
            res = MiCubacelParser._parse_data(page, bono_id)
        except IndexError:
            res = MiCubacelParser._default_data()
        return res

    @staticmethod
    def _get_promotional_bonus(page: Selector):
        bono_id = 'myStat_bonusData'
        try:
            res = MiCubacelParser._parse_data(page, bono_id)
        except IndexError:
            res = MiCubacelParser._default_data()
        return res

    @staticmethod
    def _get_lte_bonus(page: Selector):
        bono_id = 'myStat_30012'
        try:
            res = MiCubacelParser._parse_data(page, bono_id)
        except IndexError:
            res = MiCubacelParser._default_data()
        return res

    @staticmethod
    def _get_internet(page: Selector):
        bono_id = 'myStat_3001'
        try:
            data = MiCubacelParser._parse_data(page, bono_id)
            bono = page.css(f'div#{bono_id}')
            parent = bono.xpath('parent::div')
            networks = parent.css('div.network_all')
            lte, alln = ['0', 'MB'], ['0', 'MB']
            for sel in networks:
                network = sel.css('b::text').get().strip()
                value = lambda : sel.xpath('text()').get().strip().split()
                if network == "All networks:":
                    alln = value()
                elif network == "Only 4G/LTE:":
                    lte = value()
            data['only_lte'] = {'value': lte[0], 'scale': lte[1]}
            data['all_networks'] = {'value': alln[0], 'scale': alln[1]}
        except IndexError:
            data = MiCubacelParser._default_data()
            data['only_lte'] = {'value': 0, 'scale': None}
            data['all_networks'] = {'value': 0, 'scale': None}
        return data

    @staticmethod
    def _get_min_bonus(page: Selector):
        bono_id = 'myStat_bonusVOZI'
        try:
            res = MiCubacelParser._parse_data(page, bono_id)
        except IndexError:
            res = MiCubacelParser._default_data()
        return res

    @staticmethod
    def _get_sms_bonus(page: Selector):
        bono_id='myStat_bonusSMSI'
        try:
            res = MiCubacelParser._parse_data(page, bono_id)
        except IndexError:
            res = MiCubacelParser._default_data()
        return res

    @staticmethod
    def _get_money(page: Selector):
        return page.css('span.mbcHlightValue_msdp::text').get().strip()

    @staticmethod
    def _get_bonus_money(page: Selector):
        try:
            r = page.css('div.myaccount_details_block')
            r = r[-1]
            r = r.css('span.cvalue::text').get().strip()
        except (AttributeError, IndexError):
            r = '0 CUC'
        return r

    def get_data(self):
        page = self._sel
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
        # this two alway exist in the micubacel page
        r = self._get_money(page).split(' ')[0].strip()
        res['credit']['values']['credit_normal'] = {}
        res['credit']['values']['credit_normal']['cant'] = r
        r = self._get_bonus_money(page).split(' ')[0].strip()
        res['credit']['values']['credit_bonus'] = {}
        res['credit']['values']['credit_bonus']['cant'] = r
        # this services can or can't exist
        r = self._get_internet(page)
        res['data']['values']['normal'] = {}
        res['data']['values']['normal']['cant'] = to_MB(r['value'], r['scale'])
        res['data']['values']['normal']['expire'] = r['days']
        res['data']['values']['only_lte'] = {}
        res['data']['values']['only_lte']['cant'] = to_MB(r['only_lte']['value'], r['only_lte']['scale'])
        res['data']['values']['only_lte']['expire'] = r['days']
        res['data']['values']['all_networks'] = {}
        res['data']['values']['all_networks']['cant'] = to_MB(r['all_networks']['value'], r['all_networks']['scale'])
        res['data']['values']['all_networks']['expire'] = r['days']
        r = self._get_lte_bonus(page)
        res['data']['values']['lte'] = {}
        res['data']['values']['lte']['cant'] = to_MB(r['value'], r['scale'])
        res['data']['values']['lte']['expire'] = r['days']
        r = self._get_national_bonus(page)
        res['data']['values']['national_data'] = {}
        res['data']['values']['national_data']['cant'] = to_MB(r['value'], r['scale'])
        res['data']['values']['national_data']['expire'] = r['days']
        r = self._get_promotional_bonus(page)
        res['data']['values']['promotional_data'] = {}
        res['data']['values']['promotional_data']['cant'] = to_MB(r['value'], r['scale'])
        res['data']['values']['promotional_data']['expire'] = r['days']
        r = self._get_sms_bonus(page)
        res['others']['values']['sms'] = {}
        res['others']['values']['sms']['cant'] = r['value']
        res['others']['values']['sms']['unit'] = r['scale']
        res['others']['values']['sms']['expire'] = r['days']
        r = self._get_min_bonus(page)
        res['others']['values']['minutes'] = {}
        res['others']['values']['minutes']['cant'] = r['value']
        res['others']['values']['minutes']['unit'] = r['scale']
        res['others']['values']['minutes']['expire'] = r['days']
        self._result = res
        return res
