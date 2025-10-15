import asyncio

from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")

app = FastStream(broker)


# Consumer
@broker.subscriber("my-topic")
async def base_handler(body):
    print(f"Message: {body}")


# # Producer (publishing messages)
# @app.after_startup
# async def produce_messages() -> None:
#     await broker.publish("Hello from producer!", "my-topic")

if __name__ == "__main__":
    asyncio.run(app.run())
