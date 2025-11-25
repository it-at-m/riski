import asyncio
from logging import Logger

from config.config import Config, get_config
from faststream.kafka import KafkaBroker
from src.kafka.message import Message
from src.kafka.security import setup_security
from src.logtools import getLogger

logger: Logger = getLogger(__name__)
config: Config = get_config()


class LhmKafkaBroker:
    def __init__(self):
        # Security setup
        security = setup_security()

        # Kafka Broker and FastStream app setup
        broker = KafkaBroker(
            bootstrap_servers=config.kafka_server,
            security=security,
        )

        asyncio.get_event_loop().run_until_complete(broker.connect())

    async def publish(self, msg: Message):
        """
        Publish a Message to the Kafka Broker
        The topic is always lhm-riski-parse
        """
        self.broker.publish(msg, "lhm-riski-parse")
