import os
from pathlib import Path
import typer
from typing import Optional
from flask import Flask, jsonify
from pycubacel import MiCubacelConfig

fapp = Flask(__name__)
app = typer.Typer()
C_PATH = None

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

@app.command()
def consult(config_path: Optional[Path]=None):
    config_path = get_path() if config_path is None else config_path
    if config_path is None:
        raise FileNotFoundError('The config file don\'t found')
    config_path = Path(config_path)
    micubacel = MiCubacelConfig(config_path)
    return micubacel.compute_delta_and_update()

@fapp.route("/", methods=['GET'])
def hello():
    data = consult(C_PATH)
    return jsonify(data)

@fapp.route("/ping", methods=['GET'])
def ping():
    return jsonify({'status': 200})

@app.command()
def server(config_path: Optional[Path]=None):
    global C_PATH
    config_path = get_path() if config_path is None else config_path
    if config_path is None:
        raise FileNotFoundError('The config file don\'t found')
    C_PATH = config_path
    try:
        from gevent.pywsgi import WSGIServer
        print('Serving Flask app "__main__" with gevent WSGIServer')
        http_server = WSGIServer(('', 5000), fapp)
        http_server.serve_forever()
    except ImportError:
        fapp.run(host='127.0.0.1', debug=True)

def fserver():
    typer.run(server)

def fconsult():
    typer.run(consult)

if __name__ == "__main__":
    app()