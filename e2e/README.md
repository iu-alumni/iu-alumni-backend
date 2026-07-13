# ALUMAP E2E tests

Playwright + pytest browser tests for the mobile web app (Flutter Web) and,
as a supporting step, the admin dashboard. Covers two scenarios from
`E2EScenarios.md` (docs repo, `src/QA & testing/`):

- **TC1** — Registration → Login (`tests/mobile/test_auth.py`)
- **TC2** — Create Event (`tests/mobile/test_create_event.py`)

Independent of `tests/` (the backend's own unit/integration suite) — run
separately.

## Setup

```bash
cd e2e
python -m venv .venv
source .venv/bin/activate  # .venv\Scripts\activate on Windows
pip install -r requirements-e2e.txt
playwright install --with-deps chromium

cp .env.example .env  # fill in real values
```

## Running

```bash
pytest                                        # everything
pytest -m smoke                               # happy-path only
pytest -m "not negative"                      # skip validation cases
pytest --headed -v                            # watch it run
pytest --html=report.html --self-contained-html
ruff check .                                  # lint
```

With `--headed`, a failing test keeps the browser open for ~2s before
closing it, so you can actually see what was on screen.

## Layout

```
config.py       # settings from .env
conftest.py      # shared fixtures
utils/
  flutter.py      # Flutter Web quirks (see below)
  data_factory.py  # throwaway users/events per run
  admin_flows.py   # admin-panel account verification, used by TC1
pages/          # Page Object Model
  mobile/, admin/
tests/mobile/   # test_auth.py (TC1), test_create_event.py (TC2)
```

Only `test_register_then_login` registers a throwaway account — every
other test that just needs *an* existing account reuses the fixed
`TEST_ACCOUNT_EMAIL`, so it isn't coupled to registration working.

`pages/` and `utils/` include a few page objects not wired into any test
yet (map, profile, event details, admin events) — a starting point for the
remaining scenarios in `E2EScenarios.md`.

## Flutter Web gotchas

The mobile app renders to a `<canvas>` — Playwright only sees widgets once
`utils.flutter.enable_semantics()` runs (done by the `mobile_page` fixture).
After that:

- Text fields expose their hint as `aria-label`, **except** once a field
  already holds a value (no hint on a non-empty field) — those locate by
  position instead (see `login_page.py`).
- Buttons don't get a stable `role="button"` — locate by visible text
  (`utils.flutter.tap_by_text`).
- `.fill()` doesn't reliably reach Flutter's text state — use
  `utils.flutter.type_into()`.

The admin dashboard is plain HTML, but its session lives in memory, not a
cookie — `page.goto()` to another section logs you out. Navigate via the
sidebar link instead (`AdminUsersPage.goto()`).

## Known gaps

- Event creation's date/time pickers aren't automated (no stable semantic
  labels on the calendar grid); new events keep their default datetime.
- Submitting an empty event form shows no error message within timeout —
  the test only checks it didn't navigate away.
- `E2EScenarios.md`'s error-message text doesn't match what the app
  actually shows:

  | Scenario says | Actually shown |
  | --- | --- |
  | "User with this email already exists" | "Email already registered" |
  | "Wrong password or login" / "User not found" | "Incorrect email or password" |
  | "Please, specify all fields to complete the verification" | "Please enter your `<missing fields>`, and password" (dynamic) |
  | "Account banned" | "Account is banned" |

  Tests assert the real strings — please reconcile the scenario doc.
