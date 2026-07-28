"""Load test for R-04 — the single-node production server may go down under event load.

R-04 (Infrastructure risk): the production server may go down during an alumni
event because of the single-node deployment.

This simulates the read-heavy traffic alumni generate during an event —
logging in and browsing/searching the events feed — so we can measure whether
the server holds the expected peak (RPS, p95 latency, error rate) *before* the
event, which is the "pre-event load test" required by the R-04 mitigation.

Config comes from load_tests/.env (copy load_tests/.env.example → .env, which is
gitignored). Run (against the TEST SERVER, never production):

    pip install -r load_tests/requirements-load.txt
    # fill in load_tests/.env: LOAD_HOST, LOAD_EMAIL, LOAD_PASSWORD
    locust -f load_tests/locustfile.py

Then open http://localhost:8089 and set the number of users / spawn rate,
or run headless:

    locust -f load_tests/locustfile.py \
        --users 200 --spawn-rate 20 --run-time 5m --headless \
        --html load_tests/report.html

LOAD_HOST from .env is the target server; a `--host` flag on the command line
overrides it. The generated report.html is the reproducible evidence for R-04.
"""

import os

from dotenv import load_dotenv
from locust import HttpUser, between, task


# Load load_tests/.env regardless of the current working directory.
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Target server (TEST SERVER, never production). Overridable via `locust --host ...`.
LOAD_HOST = os.getenv("LOAD_HOST")
# Credentials for a seeded, verified alumni account on the target environment.
# Never hard-code real production credentials here.
LOAD_EMAIL = os.getenv("LOAD_EMAIL")
LOAD_PASSWORD = os.getenv("LOAD_PASSWORD")

API = "/api/v1"


class AlumniDuringEvent(HttpUser):
    """A single alumnus browsing the app during an event."""

    # Target from .env; a `--host` CLI flag overrides this.
    host = LOAD_HOST

    # Human-like pacing between actions.
    wait_time = between(1, 3)

    def on_start(self):
        """Authenticate once when the simulated user starts."""
        if not LOAD_EMAIL or not LOAD_PASSWORD:
            raise RuntimeError(
                "Set LOAD_EMAIL and LOAD_PASSWORD env vars to a seeded alumni account."
            )

        with self.client.post(
            f"{API}/auth/login",
            json={"email": LOAD_EMAIL, "password": LOAD_PASSWORD},
            catch_response=True,
            name="POST /auth/login",
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"login failed: {resp.status_code} {resp.text[:200]}")
                self.token = None
                return
            self.token = resp.json().get("access_token")

        if self.token:
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(5)
    def browse_events(self):
        """The dominant action during an event: opening the events feed."""
        self.client.get(f"{API}/events/?limit=50", name="GET /events (feed)")

    @task(2)
    def search_events(self):
        self.client.get(
            f"{API}/events/?search=meetup&limit=50", name="GET /events?search"
        )

    @task(1)
    def paginate_events(self):
        """Fetch first page, then follow the cursor to the second page."""
        with self.client.get(
            f"{API}/events/?limit=20",
            name="GET /events (page 1)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"feed failed: {resp.status_code}")
                return
            cursor = resp.json().get("next_cursor")
        if cursor:
            self.client.get(
                f"{API}/events/?limit=20&cursor={cursor}",
                name="GET /events (page 2)",
            )
