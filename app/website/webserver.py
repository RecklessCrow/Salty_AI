import os
import threading

from flask import Flask, render_template
from flask_sse import sse

dir_path = os.path.dirname(__file__)
app = Flask(
    __name__,
    template_folder=os.path.join(dir_path, 'templates'),
    static_folder=os.path.join(dir_path, 'static')
)
app.config['REDIS_URL'] = 'redis://redis:6379/0'
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


class WebServer:
    def __init__(self, host='0.0.0.0', port=8000):
        self.app = app
        self.thread = threading.Thread(
            target=lambda: self.app.run(host=host, port=port),
            daemon=True
        )

    def start(self):
        self.thread.start()

    def publish_event(self, web_data: dict):
        with self.app.app_context():
            sse.publish(web_data, type='update')

    def update_match_history(self, match_json: dict):
        with self.app.app_context():
            sse.publish(match_json, type='history_update')
