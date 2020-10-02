from flask import Flask, jsonify
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    f = open('data.json')
    lines = [l for l in f]
    data = json.loads(lines[-2])

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
