import asyncio

from amqtt.broker import Broker

config = {
    "listeners": {
        "default": {
            "type": "quic",
            "bind": "0.0.0.0:1883",
        },
    },
    "sys_interval": 10,
    "auth": {
        "allow-anonymous": True,
        "plugins": ["auth_anonymous"],
    },
    "topic-check": {"enabled": True, "plugins": []},
}

broker = Broker(config)


async def start_server():
    await broker.start()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_server())
    asyncio.get_event_loop().run_forever()
