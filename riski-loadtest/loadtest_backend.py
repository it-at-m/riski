# ruff: noqa: E402 (no import at top level) suppressed on this file as we need to load the environment variables before importing the app
import uuid

from truststore import inject_into_ssl

inject_into_ssl()

from gevent.pool import Pool
from locust import FastHttpUser, constant, task


class RiskiLoadtest(FastHttpUser):
    wait_time = constant(1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.host == "https://riski.muenchen.de":
            # If host is exposed to the internet we need the proxies
            self.client.proxies = {
                "http": "http://internet-proxy-client.muenchen.de:80",
                "https": "http://internet-proxy-client.muenchen.de:80",
            }
        self.client.verify = False

    @task(10)
    def generate_answer(self):
        def call_riski_api(url: str) -> None:
            payload = {
                "threadId": str(uuid.uuid4()),
                "runId": str(uuid.uuid4()),
                "tools": [],
                "context": [],
                "forwardedProps": {},
                "state": {},
                "messages": [
                    {"id": str(uuid.uuid4()), "role": "user", "content": "Welche Anträge gibt es zum Thema Radverkehr?"}
                ],
            }

            with self.client.post(url + "/api/ag-ui/riskiagent", catch_response=True, json=payload) as response:
                if response.status_code in [200, 404]:
                    response.success()
                else:
                    response.failure(f"POST {url} returned unexpected status: {response.status_code} {response.text}")

        request_pool = Pool(5)
        for _ in range(5):  # Adjust the number of requests as needed
            request_pool.spawn(call_riski_api, self.host)
        request_pool.join()

    @task(1)
    def health_check(self):
        self.client.get("/api/healthz")
