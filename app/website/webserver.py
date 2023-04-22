import os
import asyncio
import eel


class WebServer:
    def __init__(self, host='localhost', port=8000):
        self.eel = eel
        self.host = host
        self.port = port

    async def start(self):
        print(f"Starting web server on {self.host}:{self.port}")
        self.eel.init(os.path.dirname(__file__), allowed_extensions=['.js', '.html'])
        await self.eel.spawn('templates/index.html', host=self.host, port=self.port, mode='chrome-app')

    async def publish(self, content, event_type):
        if event_type == 'main':
            await self.update_main(content)
        elif event_type == 'history':
            await self.update_history(content)

    async def update_main(self, content):
        await self.eel.updateMain(content)

    async def update_history(self, content):
        await self.eel.updateHistory(content)


async def main():
    server = WebServer()
    await server.start()

if __name__ == '__main__':
    asyncio.run(main())

