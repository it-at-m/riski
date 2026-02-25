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

        cookies = {
            "ajs_user_id": "8fc0542151148372d0174415a66f10cff5a1f5c0",
            "ajs_anonymous_id": "8c2f864b-79e5-4eb7-ae23-814c50cfd3ae",
            "analytics_session_id": "1771951287072",
            "analytics_session_id.last_access": "1771951287072",
            "41e917a471a3f7ad9547afd27875fbbc": "fc30cf981a2e1f29e5251ba19f40cbc8",
            "BIGSC": "!mg5TwJqGFPLYzYiw6q1zOJj8NrwSwMdldCwO5fWd8RWoFT65acqtiIXdaa5FMnmbBCECYC/oLroju5o=",
        }

        logger.info(f"Request {config.request_url}")
        response = client.post(url=config.request_url, json=payload, cookies=cookies)
        logger.info(f"Request Finished {response.status_code}")
        time.sleep(config.request_interval)


if __name__ == "__main__":
    sys.exit(main())
