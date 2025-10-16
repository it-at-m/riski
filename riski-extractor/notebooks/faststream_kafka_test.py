import asyncio
import time

from faststream import FastStream
from faststream.kafka import KafkaBroker
from pydantic import BaseModel

broker = KafkaBroker("localhost:9092")

app = FastStream(broker)


class Message(BaseModel):
    content: str
    republished: bool = False


# Consumer, getting all messages already in the topic, but only once for set group id
@broker.subscriber("my-topic", auto_offset_reset="earliest", group_id="my-group")
async def base_handler(msg: Message):
    if msg.republished:
        print("Republished Message:")
    print(f"Message: {msg.content}")
    time.sleep(2)
    if msg.content == "error message" and not msg.republished:
        print("Simulating error, republishing message...")
        msg.republished = True
        await broker.publish(msg, "my-topic")


# # Producer (publishing messages)
# @app.after_startup
# async def produce_messages() -> None:
#     await broker.publish("Hello from producer!", "my-topic")

if __name__ == "__main__":
    asyncio.run(app.run())
