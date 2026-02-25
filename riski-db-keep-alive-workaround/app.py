import sys
import time
import uuid
from logging import Logger

from config.config import Config, get_config
from httpx import Client

from src.logtools import getLogger

logger: Logger
config: Config


def main():
    config = get_config()
    config.print_config()
    logger = getLogger()
    logger.info("DB Keep Alive Service starting up")

    client = Client(verify=False)

    while True:
        payload = {
            "threadId": str(uuid.uuid4()),
            "runId": str(uuid.uuid4()),
            "tools": [],
            "context": [],
            "forwardedProps": {},
            "state": {},
            "messages": [{"id": str(uuid.uuid4()), "role": "user", "content": "Welche Anträge gibt es zum Thema Radverkehr?"}],
        }

        logger.info(f"Request {config.request_url}")
        response = client.post(url=config.request_url, json=payload)
        logger.info(f"Request Finished {response.status_code}")
        time.sleep(config.request_interval)


if __name__ == "__main__":
    sys.exit(main())
