import os
import eel


class WebServer:
    def __init__(self, host='0.0.0.0', port=8000):
        self.eel = eel
        self.host = host
        self.port = port

    def start(self):
        print(f"Starting web server on {self.host}:{self.port}")
        self.eel.init(os.path.dirname(__file__), allowed_extensions=['.js', '.html'])
        self.eel.start(
            'templates/index.html',
            host=self.host,
            port=self.port,
            templates="templates",
            mode='chrome-app',
            block=False
        )
        self.eel.sleep(1)

    def publish(self, content, event_type):
        match event_type:
            case 'main':
                self.update_main(content)
            case 'history':
                self.update_history(content)
        self.eel.sleep(1)

    def update_main(self, content):
        self.eel.updateMain(content)

    def update_history(self, content):
        self.eel.updateHistory(content)



