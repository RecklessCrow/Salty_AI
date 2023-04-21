import json
import os

from flask import Flask, render_template, jsonify
from flask_sse import sse

from utils.websettings import settings

dir_path = os.path.dirname(__file__)
print(dir_path)
app = Flask(
    __name__,
    template_folder=os.path.join(dir_path, 'templates'),
    static_folder=os.path.join(dir_path, 'static')
)
app.register_blueprint(sse, url_prefix='/stream')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/style.css')
def serve_css():
    return app.send_static_file("style.css")


@app.route('/script.js')
def serve_js():
    return app.send_static_file("script.js")


def publish_event(data):
    sse.publish(data, type='update')


@app.route('/data')
def data():
    with open(settings.JSON_PATH) as f:
        data = json.load(f)
    return jsonify(data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
