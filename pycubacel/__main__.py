import os
from pathlib import Path
from typing import Optional
import typer
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
    return None


@app.command()
def consult(config_path: Path = typer.Argument(
        default=None,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True)):
    micubacel = MiCubacelConfig(config_path)
    return micubacel.compute_delta_and_update()


@ fapp.route("/", methods=['GET'])
def hello():
    data = consult(C_PATH)
    return jsonify(data)


@ fapp.route("/ping", methods=['GET'])
def ping():
    return jsonify({'status': 200})


@ app.command()
def server(config_path: Path = typer.Argument(
    default=None,
    exists=True,
    file_okay=True,
    dir_okay=False,
    readable=True,
    resolve_path=True)):
    global C_PATH
    C_PATH = str(config_path)
    MiCubacelConfig(config_path)
    try:
        from gevent.pywsgi import WSGIServer
        print('Serving Flask app "__main__" with gevent WSGIServer')
        http_server = WSGIServer(('0.0.0.0', 5000), fapp)
        http_server.serve_forever()
    except ImportError:
        fapp.run(host='0.0.0.0', debug=True)


def fserver():
    typer.run(server)


def fconsult():
    typer.run(consult)


if __name__ == "__main__":
    app()
