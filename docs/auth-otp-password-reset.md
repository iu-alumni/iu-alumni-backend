# OTP Login & Password Reset — Client Integration Guide

This document describes the two new optional authentication features and how to integrate them on the client side.

---

## 1. OTP Login

A passwordless-style second-factor login. The user proves ownership of their university email by entering a time-limited 6-digit code. This is **optional** — the standard `POST /auth/login` (password → JWT) continues to work unchanged.

### Flow

```
Client                              Server
  │                                   │
  │─── POST /auth/login/otp/request ──►│  validates email+password
  │                                   │  sends 6-digit code to email
  │◄── { session_token, message } ────│
  │                                   │
  │  (user reads code from email)     │
  │                                   │
  │─── POST /auth/login/otp/verify ───►│  validates session_token + code
  │◄── { access_token, token_type } ──│  returns JWT
```

### Step 1 — Request OTP code

**`POST /auth/login/otp/request`**

Request body:
```json
{
  "email": "a.student@innopolis.university",
  "password": "mypassword"
}
```

Success response `200`:
```json
{
  "session_token": "3f7a1b2c-...",
  "message": "A verification code has been sent to a.student@innopolis.university"
}
```

Store `session_token` in memory — you'll need it in step 2.

#### Error responses

| Status | Detail | Meaning |
|--------|--------|---------|
| `401` | `Incorrect email or password` | Wrong credentials |
| `401` | `Account not verified` | User hasn't completed registration |
| `401` | `Account is banned` | Account is suspended |
| `429` | `Please wait N seconds before requesting a new code` | Cooldown active (60s between requests) |

---

### Step 2 — Verify OTP code

**`POST /auth/login/otp/verify`**

Request body:
```json
{
  "session_token": "3f7a1b2c-...",
  "code": "482910"
}
```

Success response `200`:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

Use `access_token` as a Bearer token on all subsequent authenticated requests.

#### Error responses

| Status | Detail | Meaning |
|--------|--------|---------|
| `401` | `Invalid or expired session` | `session_token` unknown or already used |
| `401` | `Verification code has expired` | Code older than `LOGIN_CODE_EXPIRY_MINUTES` (default 10 min) |
| `401` | `Incorrect verification code. N attempt(s) remaining` | Wrong code — up to 5 tries |
| `429` | `Too many incorrect attempts. Please request a new code` | 5 failed attempts, session invalidated |

---

### Rate limiting rules

- One OTP code per account per **60 seconds** — repeated `POST /otp/request` within this window returns `429`.
- A `session_token` is **single-use** and valid for `LOGIN_CODE_EXPIRY_MINUTES` (default: **10 minutes**).
- After **5 wrong code submissions**, the session is permanently invalidated — the user must call `otp/request` again.

---

## 2. Password Reset

Allows a user to recover access to their account without admin intervention by receiving a unique reset link in their university email.

### Flow

```
Client                                   Server
  │                                        │
  │─── POST /auth/password-reset/request ──►│  looks up email (silent if not found)
  │◄── { message } ────────────────────────│  sends reset link email
  │                                        │
  │  (user clicks link in email)           │
  │  frontend extracts ?token=<uuid>       │
  │                                        │
  │─── POST /auth/password-reset/confirm ──►│  validates token
  │◄── { message } ────────────────────────│  updates password
```

### Step 1 — Request reset link

**`POST /auth/password-reset/request`**

Request body:
```json
{
  "email": "a.student@innopolis.university"
}
```

Response `200` (always — even if email not registered):
```json
{
  "message": "If that email is registered, a reset link has been sent"
}
```

> **Always show the same message** regardless of whether the email exists. This prevents account enumeration.

The email contains a link in the form:
```
https://<MINI_APP_URL>/reset-password?token=<uuid>
```

Your reset-password page must extract the `token` query parameter and pass it to step 2.

#### Error responses

This endpoint has no error responses by design (always `200`). Rate limiting is enforced silently.

---

### Step 2 — Confirm new password

**`POST /auth/password-reset/confirm`**

Request body:
```json
{
  "token": "d4e5f6a7-...",
  "new_password": "mynewpassword123"
}
```

Success response `200`:
```json
{
  "message": "Password updated successfully"
}
```

#### Error responses

| Status | Detail | Meaning |
|--------|--------|---------|
| `400` | `Invalid or already used reset token` | Token not found or already consumed |
| `400` | `Reset token has expired` | Token older than `PASSWORD_RESET_EXPIRY_MINUTES` (default 30 min) |
| `429` | `Too many incorrect attempts. Please request a new reset link` | 5 failed attempts |

---

### Rate limiting rules

- One reset link per account per **60 seconds** (enforced silently — always returns `200`).
- A reset token is **single-use** and valid for `PASSWORD_RESET_EXPIRY_MINUTES` (default: **30 minutes**).
- After **5 failed submissions**, the token is invalidated — user must request a new link.
- `new_password` must be at least **8 characters**.

---

## Environment variables (server-side)

| Variable | Default | Description |
|---|---|---|
| `LOGIN_CODE_EXPIRY_MINUTES` | `10` | How long an OTP code is valid |
| `PASSWORD_RESET_EXPIRY_MINUTES` | `30` | How long a reset link is valid |

---

## Client implementation checklist

### OTP Login
- [ ] Add "Login with email code" option on login screen
- [ ] Call `POST /auth/login/otp/request` with email + password
- [ ] Store `session_token` in memory (not persistent storage)
- [ ] Show code input screen, display remaining time (10 min)
- [ ] Call `POST /auth/login/otp/verify` with `session_token` + code
- [ ] Handle `429` on request → show cooldown timer using seconds from error message
- [ ] Handle `401` with remaining attempts → show attempts counter
- [ ] Handle `429` on verify → send user back to request screen

### Password Reset
- [ ] Add "Forgot password?" link on login screen
- [ ] Collect email and call `POST /auth/password-reset/request`
- [ ] Always show the same success message regardless of response
- [ ] Create `/reset-password` route that reads `?token=` from URL
- [ ] Show new password form (min 8 chars, confirmation field)
- [ ] Call `POST /auth/password-reset/confirm` with `token` + `new_password`
- [ ] On success → redirect to login with success message
- [ ] Handle `400` (expired/invalid) → show "link expired, request new one"
