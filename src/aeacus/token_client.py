import asyncio

from amqtt.client import MQTTClient
from amqtt.mqtt.constants import QOS_0

topic = 'aeacus'
# url = "mqtt://195.148.127.230"
url = "mqtt://127.0.0.1"


async def run_sub():
    client = MQTTClient()
    await client.connect(url)
    await client.subscribe([(topic, QOS_0)])
    while True:
        print("Waiting for the next message")
        msg = await client.deliver_message()
        pkt = msg.publish_packet
        print(f'Receive msg: {pkt}')


async def run_pub():
    client = MQTTClient()
    await asyncio.sleep(1)
    await client.connect(url)
    for i in range(10):
        await client.publish(topic, "test".encode())
        print(f'Sent msg: test')
        await asyncio.sleep(1)
    await client.disconnect()
    print(f'Disconnected')


async def main():
    asyncio.create_task(run_sub())
    asyncio.create_task(run_pub())
    await asyncio.sleep(1000)


if __name__ == "__main__":
    asyncio.run(main())
