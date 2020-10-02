from micubacel import consult
from flask import Flask, jsonify
from pathlib import Path

app = Flask(__name__)

@app.route("/", methods=['GET'])
def hello():
    data = consult(Path('./config.json'))
    return jsonify(data)

@app.route("/ping", methods=['GET'])
def ping():
    return jsonify({'status': 200})

if __name__ == "__main__":
    app.run(host='127.0.0.1', debug=True)
