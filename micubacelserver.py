from micubacel import consult
from flask import Flask, jsonify
from pathlib import Path

# openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

app = Flask(__name__)

@app.route("/", methods=['GET'])
def hello():
    data = consult(Path('./config.json'))
    return jsonify(data)

if __name__ == "__main__":
	#app.run(host='127.0.0.1', debug=True, ssl_context=('cert.pem', 'key.pem'))
    app.run(host='127.0.0.1', debug=True)