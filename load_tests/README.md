# Load testing — R-04 pre-event load test

This directory holds the load test that covers **risk R-04** (Infrastructure):

> Production server **may go down** during an alumni event (single-node
> deployment = single point of failure) → users can't register/participate.

The R-04 mitigation requires a **pre-event load test** to confirm the server
holds the expected peak. This is that test.

## What it simulates

`locustfile.py` models an alumnus during an event: log in once, then repeatedly
browse and search the events feed (the dominant read traffic during an event).
It reports RPS, latency percentiles (p50/p95/p99) and error rate.

## Prerequisites

- A **test server** environment reachable over HTTP(S). **Never run against
  production** — a load test can itself cause the outage it's meant to predict.
- A seeded, verified alumni account on that environment.

## Configure

Copy the template and fill in real values (`load_tests/.env` is gitignored):

```bash
cp load_tests/.env.example load_tests/.env
# edit load_tests/.env:
#   LOAD_HOST=https://test.example.com   # test server, never production
#   LOAD_EMAIL / LOAD_PASSWORD              # a seeded verified alumni account
```

## Run

```bash
pip install -r load_tests/requirements-load.txt

# Interactive (web UI at http://localhost:8089):
locust -f load_tests/locustfile.py

# Headless, with an HTML report (the R-04 evidence artifact):
locust -f load_tests/locustfile.py \
    --users 200 --spawn-rate 20 --run-time 5m --headless \
    --html load_tests/report.html
```

`LOAD_HOST` from `.env` is the target; a `--host <url>` flag overrides it.
Pick `--users` to match the expected peak concurrent alumni for the event.

## Interpreting results (pass/fail for R-04)

Suggested thresholds (align with QR3 in the Quality Plan, p95 < 500ms):

| Metric | Target |
| --- | --- |
| Error rate | 0% (no 5xx) |
| p95 latency | < 500 ms |
| Sustained RPS | ≥ expected peak |

If the run reveals a capacity limit below the expected peak, that triggers the
R-04 contingency: present the Alumni Office with options (A accept current
capacity vs B scale-up for the event) and record their decision before the
event.

Save `report.html` as the reproducible evidence for the R-04 mitigation.
