import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any, Final

from faststream import AckPolicy, BaseMiddleware, Context, FastStream, StreamMessage
from faststream.kafka import KafkaBroker, KafkaMessage
from pydantic import BaseModel


class MessageBody(BaseModel):
    content: str
    republished: bool = False


class RetryDLQMiddleware(BaseMiddleware):
    MAX_RETRIES: Final[int] = 3
    DLQ_TOPIC: Final[str] = "my-topic-dlq"

    async def consume_scope(self, call_next: Callable[[StreamMessage[Any]], Awaitable[Any]], msg: StreamMessage[Any]) -> Any:
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return await call_next(msg)
            except Exception:
                if attempt == self.MAX_RETRIES:
                    print("Max retries exhausted, sending to DLQ")
                    # Access broker from context
                    broker = self.context.get_local("broker")
                    # Publish to DLQ
                    await broker.publish(msg.body, self.DLQ_TOPIC)
                    raise
                print(f"Retrying message, attempt {attempt + 1}")
                await asyncio.sleep(2**attempt)


broker = KafkaBroker("localhost:9092", middlewares=[RetryDLQMiddleware])
app = FastStream(broker)


# Consumer, getting all messages already in the topic, but only once for set group id
@broker.subscriber("my-topic", auto_offset_reset="earliest", group_id="my-group", ack_policy=AckPolicy.ACK)
async def base_handler(body: MessageBody, msg: KafkaMessage, headers: str = Context("message.headers")) -> None:
    if body.republished:
        print("Republished Message:")
    print(f"Message id: {msg.message_id}")
    print(f"Message committed: {msg.committed}")
    print(f"Message headers: {headers}")
    print(f"Message: {body.content}")
    time.sleep(2)
    if body.content == "error message":
        print("Simulating error")
        raise Exception


@broker.subscriber("my-topic-dlq", group_id="dlq-consumer")
async def dlq_handler(msg_body: MessageBody, msg: KafkaMessage, headers: str = Context("message.headers")) -> None:
    print(f"DLQ received: {msg_body.content}, headers: {headers}")
    print(f"Message id: {msg.message_id}")


# # Producer (publishing messages)
# @app.after_startup
# async def produce_messages() -> None:
#     await broker.publish("Hello from producer!", "my-topic")

if __name__ == "__main__":
    asyncio.run(app.run())
