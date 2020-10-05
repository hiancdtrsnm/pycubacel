import os
import json
import datetime
from pathlib import Path
from typing import Union, Dict, Any
import warnings
from urllib3.connectionpool import InsecureRequestWarning
import requests
from parsel import Selector
from .costants import HEADERS, LOGIN_FORM
from .utils import load_cookies, dump_cookies, bound_float, validate_phone
from .parser import MiCubacelParser
from .exceptions import BadCredentials, IcorrectUsernameFormat
from .jsonline import jsonLine

warnings.filterwarnings('ignore', category=InsecureRequestWarning)


class MiCubacel:
    url_login = 'https://mi.cubacel.net:8443/login/Login'
    url_base = 'https://mi.cubacel.net'

    def __init__(self, username: str, password: str, cookies: Dict[str, Any]={}):
        if not validate_phone(username):
            raise IcorrectUsernameFormat(f"The format must be the number 5 plus seven number. \
                                            The expression \"{username}\" don't match with this format.")
        self._ss = requests.Session()
        for i, j in HEADERS.items():
            self._ss.headers[i] = j
        self._ss.verify = False
        self._username = username
        self._password = password
        self._cookies_ok = load_cookies(self._ss, cookies)
        self._login_form = {i: j for i, j in LOGIN_FORM.items()}
        self._login_form['username'] = username
        self._login_form['password'] = password

    @property
    def cookies(self):
        return dump_cookies(self._ss.cookies)

    def set_cookies(self, cookies):
        return load_cookies(self._ss, cookies)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ss.close()

    def _post(self, url, data):
        ss = self._ss
        ss.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        res = ss.post(url, data=data, verify=False)
        ss.headers.pop('Content-Type')
        return res

    def get_data(self):
        ss = self._ss
        if not self._cookies_ok:
            res = ss.post(self.url_login, data=self._login_form, verify=False)
            if not MiCubacelParser.page_ok(res.text):
                raise BadCredentials()
        resp = ss.get(self.url_base, verify=False).text
        url = MiCubacelParser.lang_url(resp)
        resp = ss.get(url)
        url = MiCubacelParser.my_account(resp.text)
        resp = ss.get(url)
        page = MiCubacelParser(resp.text)
        return page

    def consult(self, print_data=True):
        return self.get_data().data

class MiCubacelConfig(MiCubacel):

    def __init__(self, config_path: Union[str, Path]):
        config_path = Path(config_path)
        self._config_path = config_path
        config = json.load(config_path.open())
        self._config = config
        cookies_path = os.path.expandvars(os.path.expanduser(config['cookies_path']))
        cookies_path = cookies_path+'.'+config['login']['username']
        self._cookies_path = cookies_path
        if os.path.exists(cookies_path):
            cookies = json.load(open(cookies_path))
        else:
            cookies = {}
        username = config['login']['username']
        password = config['login']['password']
        super().__init__(username, password, cookies=cookies)

    def consult(self, print_data=True):
        if self._cookies_ok:
            json.dump(self.cookies, open(self._cookies_path, 'w'), indent=2)
        ans = {}
        start = datetime.datetime.now()
        page = self.get_data()
        ans['internet'] = page.data
        ans['duration'] = str(datetime.datetime.now() - start)
        ans['timestamp'] = str(datetime.datetime.now())
        ans['user'] = self._username
        if print_data:
            self.print_data(page)
        try:
            jpth = os.path.expanduser(self._config['data_path']).rsplit('.', 1)[0]
            consults = jsonLine(jpth, default=str)
            consults.append(ans)
            #with open(os.path.expanduser(self._config['data_path']), 'a') as f:
            #    f.write(json.dumps(ans, default=str, ensure_ascii=False) + '\n')
        except Exception as e:
            print(e)
        return ans

    @staticmethod
    def print_data(page: MiCubacelParser):
        data = page.data
        r = data['credit']['values']['credit_normal']['cant']
        print("Credit:", r)
        r = data['credit']['values']['credit_bonus']['cant']
        print("Credit Bonus:", r)
        r = data['others']['values']['minutes']
        print("Minute Bonus:", r['cant'], r['unit'], 'expire', r['expire'])
        r = data['others']['values']['sms']
        print("SMS Bonus:", r['cant'], r['unit'], 'expire', r['expire'])
        r = data['data']['values']
        print("Internet, expire", r['normal']['expire'], ':')
        print('  LTE only:', r['only_lte']['cant'], 'MB')
        print('  All networks:', r['all_networks']['cant'], 'MB')
        print("LTE Bonus:", r['lte']['cant'], 'MB expire', r['lte']['expire'])
        print("National Bonus:", r['national_data']['cant'], 'MB', 'expire in', r['national_data']['expire'])

    def compute_delta_and_update(self):
        odata = self.consult(print_data=False)
        data = odata['internet']
        jpth = os.path.expanduser(self._config['data_path']).rsplit('.', 1)[0]
        consults = jsonLine(jpth)
        try:
            last = consults[-2]['internet']
        except:
            odata = self.consult(print_data=False)
            data = odata['internet']
            consults = jsonLine(jpth)
            last = consults[-2]['internet']
        for i in data.keys():
            for j in data[i]['values'].keys():
                #try:
                delta = float(data[i]['values'][j]['cant'])-float(last[i]['values'][j]['cant'])
                #except KeyError:
                #    delta = 0
                print(delta)
                data[i]['values'][j]['delta'] = bound_float(delta)
        r = data['credit']['values']['credit_normal']
        print("Credit:", r['cant'], f" delta={r['delta']}")
        r = data['credit']['values']['credit_bonus']
        print("Credit Bonus:", r['cant'], f" delta={r['delta']}")
        r = data['others']['values']['minutes']
        print("Minute Bonus:", r['cant'], r['unit'], 'expire', r['expire'], f" delta={r['delta']}")
        r = data['others']['values']['sms']
        print("SMS Bonus:", r['cant'], r['unit'], 'expire', r['expire'], f" delta={r['delta']}")
        r = data['data']['values']
        print("Internet, expire", r['normal']['expire'], ':')
        print('  LTE only:', r['only_lte']['cant'], 'MB', f" delta={r['only_lte']['delta']}")
        print('  All networks:', r['all_networks']['cant'], 'MB', f" delta={r['all_networks']['delta']}")
        print("LTE Bonus:", r['lte']['cant'], 'MB expire', r['lte']['expire'], f" delta={r['lte']['delta']}")
        print("Promotional Bonus:", r['promotional_data']['cant'], 'MB', 'expire in', r['promotional_data']['expire'], f" delta={r['promotional_data']['delta']}")
        print("National Bonus:", r['national_data']['cant'], 'MB', 'expire in', r['national_data']['expire'], f" delta={r['national_data']['delta']}")
        odata['internet'] = data
        return odata
