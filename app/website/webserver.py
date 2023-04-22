import os
import threading

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

dir_path = os.path.dirname(__file__)
app = Flask(
    __name__,
    template_folder=os.path.join(dir_path, 'templates'),
    static_folder=os.path.join(dir_path, 'static')
)
socketio = SocketIO(app)


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
            target=lambda: socketio.run(self.app, host=host, port=port),
            daemon=True
        )

    def start(self):
        self.thread.start()

    @socketio.on('publisher')
    def publish(self, content, socket_id):
        emit(socket_id, content)
