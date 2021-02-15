import os
import sys

from flask import Flask, jsonify

from pycubacel import MiCubacelConfig

fapp = Flask(__name__)


def get_path():
    if os.path.exists('./micubacel_config.json'):
        return './micubacel_config.json'
    if os.path.exists('./config.json'):
        return './config.json'
    pth = os.path.expandvars(os.path.expanduser('~/.micubacel_config.json'))
    if os.path.exists(pth):
        return pth
    pth = os.path.expandvars(os.path.expanduser('~/.config.json'))
    if os.path.exists(pth):
        return pth
    return None


C_PATH = get_path()


@fapp.route("/", methods=['GET'])
def hello():
    micubacel = MiCubacelConfig(C_PATH)
    data = micubacel.compute_delta_and_update()
    return jsonify(data)


@fapp.route("/ping", methods=['GET'])
def ping():
    return jsonify({'status': 200})


if __name__ == "__main__":
    try:
        from gevent.pywsgi import WSGIServer
        print('Serving Flask app "__main__" with gevent WSGIServer')
        http_server = WSGIServer(('0.0.0.0', 5000), fapp, log=sys.stdout)
        http_server.serve_forever()
    except ImportError:
        fapp.run(host='0.0.0.0', debug=True, log=sys.stdout)
