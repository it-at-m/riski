import asyncio

from config.config import Config, get_config
from faststream.kafka import KafkaBroker
from src.kafka.message import Message
from src.kafka.security import setup_security
from src.logtools import getLogger

config: Config = get_config()


class LhmKafkaBroker:
    def __init__(self):
        # Security setup
        self.security = setup_security()
        self.logger = getLogger(__name__)
        # Kafka Broker and FastStream app setup
        self.broker = KafkaBroker(
            bootstrap_servers=config.kafka_server,
            security=self.security,
        )
        self.logger.debug("Connecting to Broker...")
        asyncio.run(self.broker.connect())
        self.logger.info("Broker connected.")

    def publish(self, msg: Message):
        """
        Publish a Message to the Kafka Broker.
        The topic can be set via config.
        """
        self.logger.debug(f"Publishing: {msg}.")
        asyncio.run(self.broker.publish(msg, topic=config.kafka_topic))
        self.logger.debug(f"Published: {msg}.")
