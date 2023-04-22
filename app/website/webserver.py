import os
import threading
import eel


class WebServer:
    def __init__(self, host='0.0.0.0', port=8000):
        self.thread = threading.Thread(
            target=lambda: self._run(host, port),
            daemon=True
        )

    @staticmethod
    def _run(host, port):
        eel.init(os.path.dirname(__file__), allowed_extensions=['.js', '.html'])
        eel.start('index.html', host=host, port=port)

    def start(self):
        self.thread.start()

    def publish(self, content, event_type):
        if event_type == 'main':
            self.update_main(content)
        elif event_type == 'history':
            self.update_history(content)

    def update_main(self, content):
        eel.update_main(content)

    def update_history(self, content):
        eel.update_history(content)
