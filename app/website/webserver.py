import os
import eel


class WebServer:
    def __init__(self, host='localhost', port=8000):
        self.eel = eel
        self.host = host
        self.port = port

    def start(self):
        print(f"Starting web server on {self.host}:{self.port}")
        self.eel.init(os.path.dirname(__file__), allowed_extensions=['.js', '.html'])
        self.eel('templates/index.html', host=self.host, port=self.port, mode='chrome-app', block=False)

    def publish(self, content, event_type):
        if event_type == 'main':
            self.update_main(content)
        elif event_type == 'history':
            self.update_history(content)

    def update_main(self, content):
        self.eel.updateMain(content)

    def update_history(self, content):
        self.eel.updateHistory(content)



