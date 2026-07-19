# ALUMAP E2E tests

Playwright + pytest browser tests for the mobile web app (Flutter Web) and,
as a supporting step, the admin dashboard. Covers scenarios from
`E2EScenarios.md` (docs repo, `src/QA & testing/`):

- **TC1** — Registration → Login (`tests/mobile/test_auth.py`)
- **TC2** — Create Event (`tests/mobile/test_create_event.py`)
- **TC3** — Map Loading (`tests/mobile/test_map.py`)
- **TC4** — Admin: Approve Event (`tests/admin/test_approve_event.py`)
- **TC5** — Empty Fields Validation (`tests/mobile/test_form_validation.py`)
- **TC6** — Edit Profile (`tests/mobile/test_profile.py`)
- **TC7** — Admin: Verify / Ban User (`tests/admin/test_users.py`)
- **TC8** — View Event Details (`tests/mobile/test_event_details.py`)

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
tests/
  mobile/         # test_auth.py (TC1), test_create_event.py (TC2), test_map.py (TC3),
                  # test_form_validation.py (TC5), test_profile.py (TC6),
                  # test_event_details.py (TC8)
  admin/          # test_approve_event.py (TC4), test_users.py (TC7)
```

Only `test_register_then_login` registers a throwaway account — every
other test that just needs *an* existing account reuses the fixed
`TEST_ACCOUNT_EMAIL`, so it isn't coupled to registration working. TC4 and
TC7 create their own throwaway account/event the same way, through the
real mobile UI in an isolated browser context
(`utils.admin_flows.create_event_via_mobile` /
`register_alumnus_via_mobile`) — TC7 specifically needs *unverified*
accounts to act on, so it can't reuse the fixed one. TC6 edits that shared
account's name, so it captures the original first/last name up front and
restores it in a `finally` block — the app requires both fields non-empty
to save, and the account's last name started blank, so restoring falls
back to a real value instead of resaving it blank.

TC7's ban case verifies the account before banning it — confirmed live
that the backend checks verification *before* ban status, so an
unverified-and-banned account shows "Account not verified" regardless,
never reaching the "banned" message.

`pages/` and `utils/` include a few page objects not wired into any test
yet (event details beyond TC4, admin users) — a starting point for
the remaining scenarios in `E2EScenarios.md`.

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
- The bottom tab bar (map/events/profile) has no text or labels at all —
  `RootNavigation` taps fixed screen coordinates instead, and retries the
  tap (up to 3x) against a screen-specific marker for events/profile —
  confirmed live that a single coordinate tap occasionally misses.
- A tiled map never goes network-idle (tile servers keep chattering) —
  `MobileMapPage.expect_tile_load()` waits for the first actual tile
  response instead of `networkidle`.

The admin dashboard is plain HTML. Its auth token lives in `localStorage`
(a plain `page.reload()` keeps you logged in), but `ADMIN_BASE_URL` already
includes `/dashboard`, so naively appending a path (`f"{base}/users"`)
produces an invalid nested route — navigate via the sidebar link instead
(`AdminUsersPage.goto()` / `AdminEventsPage.goto()`), and use `.refresh()`
to reload the current section rather than re-navigating to it.

Some of this admin data loads async *after* mount with a `false`/"Off"
default in the meantime (e.g. `isVerificationEnabled` in
`events/index.vue`) — reading a toggle's state right after navigating can
catch that default instead of the real value, silently corrupting global
settings that are shared with everyone else on `tst`. Confirmed live this
caused `set_auto_approve()` to occasionally read the wrong state and flip
it wrong. `AdminEventsPage.refresh()` waits for the actual settings
response, not just for some button to render, before returning.

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
