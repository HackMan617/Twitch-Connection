import twitchio
from twitchio.ext import commands
import time
import concurrent.futures
import traceback
import asyncio

class TwitchPlaysConnection:
    def __init__(self, config):
        self.config = config
        self.session = None
        self.fetch_job = None
        self.next_fetch_time = time.time()
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.bot = commands.Bot(
            irc_token=self.config['wss://irc-ws.chat.twitch.tv:443'],
            #client_id=self.config['gp762nuuoqcoxypju8c569th9wz7q5'],
            #nick=self.config['HackMan617'],
           # prefix=self.config['Hack'],
           # initial_channels=[self.config['HackMan617']]
        )

    def connect(self):
        # Establish connection to Twitch chat
        pass

    def reconnect(self, delay):
        # Reconnect after a delay
        time.sleep(delay)
        self.connect()

    def fetch_messages(self):
        # Fetch messages from Twitch chat
        pass

    def parse_messages(self, res):
        messages = []
        try:
            for action in res['actions']:
                if 'item' in action['addChatItemAction']:
                    if 'liveChatTextMessageRenderer' in action['addChatItemAction']['item']:
                        item = action['addChatItemAction']['item']['liveChatTextMessageRenderer']
                        messages.append({
                            'author': item['authorName']['simpleText'],
                            'content': item['message']['runs']
                        })
            return messages
        except Exception as e:
            print(f"Failed to parse messages.")
            print("Body:", res.text)
            traceback.print_exc()
        return []

    def twitch_receive_messages(self):
        if self.session is None:
            self.reconnect(0)
        messages = []
        if not self.fetch_job:
            time.sleep(1.0 / 60.0)
            if time.time() > self.next_fetch_time:
                self.fetch_job = self.thread_pool.submit(self.fetch_messages)
        else:
            res = []
            timed_out = False
            try:
                res = self.fetch_job.result(1.0 / 60.0)
            except concurrent.futures.TimeoutError:
                timed_out = True
            except Exception:
                traceback.print_exc()
                self.session.close()
                self.session = None
                return
            if not timed_out:
                self.fetch_job = None
                self.next_fetch_time = time.time() + self.config['fetch_interval']
            for item in res:
                msg = {
                    'username': item['author'],
                    'message': ''
                }
                for part in item['content']:
                    if 'text' in part:
                        msg['message'] += part['text']
                    elif 'emoji' in part:
                        msg['message'] += part['emoji']['emojiId']
                messages.append(msg)
        return messages

    async def send_message(self, message):
        channel = self.bot.get_channel(self.config['twitch_channel'])
        if channel:
            await channel.send(message)

    def close(self):
        # Close the connection
        if self.session:
            self.session.close()
            self.session = None

    async def input_loop(self):
        while True:
            user_input = input("Enter message to send to Twitch chat: ")
            await self.send_message(user_input)

# Example usage
if __name__ == "__main__":
    config = {
        'twitch_irc_token': 'your_irc_token',
        'twitch_client_id': 'your_client_id',
        'twitch_nick': 'your_twitch_nickname',
        'twitch_prefix': '!',
        'twitch_channel': 'your_channel_name',
        'fetch_interval': 5  # Example interval
    }

    connection = TwitchPlaysConnection(config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connection.input_loop())