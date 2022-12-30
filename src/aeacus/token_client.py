import asyncio

from amqtt.client import MQTTClient, ConnectException
from amqtt.mqtt.constants import QOS_1, QOS_2


config = {
    "aeacus": {
        "topic": "/aeacus/token",
        "message": b"Dead or alive",
        "qos": 0x01,
        "retain": True,
    }
}


async def test_coro():
    C = MQTTClient(config=config)
    await C.connect("mqtt://test.mosquitto.org/")
    tasks = [
        asyncio.ensure_future(C.publish("a/b", b"TEST MESSAGE WITH QOS_0")),
        asyncio.ensure_future(C.publish("a/b", b"TEST MESSAGE WITH QOS_1", qos=QOS_1)),
        asyncio.ensure_future(C.publish("a/b", b"TEST MESSAGE WITH QOS_2", qos=QOS_2)),
    ]
    await asyncio.wait(tasks)
    print("messages published")
    await C.disconnect()


async def test_coro2():
    try:
        C = MQTTClient()
        await C.connect("mqtt://localhost:1883/")
        await C.publish("a/b", b"TEST MESSAGE WITH QOS_0", qos=0x00)
        await C.publish("a/b", b"TEST MESSAGE WITH QOS_1", qos=0x01)
        await C.publish("a/b", b"TEST MESSAGE WITH QOS_2", qos=0x02)
        print("messages published")
        await C.disconnect()
    except ConnectException as ce:
        print("Connection failed: %s" % ce)
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(test_coro())
    asyncio.get_event_loop().run_until_complete(test_coro2())
