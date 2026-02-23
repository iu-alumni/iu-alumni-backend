# IU Alumni — Backend

FastAPI service providing the REST API and Telegram bot integration for the IU Alumni platform.

## Tech Stack

- **Python 3.11** · **FastAPI 1.0** · **SQLAlchemy** (ORM) · **Alembic** (migrations)
- **PostgreSQL** · **MinIO** (object storage) · **uv** (package manager)

## API

| Route group | Description |
|---|---|
| `/auth` | Registration, login, JWT token refresh |
| `/profile` | User profile read/update |
| `/events` | Alumni events CRUD |
| `/cities` | City listing |
| `/telegram` | Telegram bot webhook |
| `/admin` | User management, email allowlist, event moderation |

> Interactive docs (`/docs`, `/redoc`) are only available when `ENVIRONMENT=DEV`.

## Local Development

```bash
cp .env.example .env  # fill in values
docker compose up
```

API available at `http://localhost:8080`.

### Running cron jobs locally

```bash
docker compose -f docker-compose.cron.yml up
```

## Deployment

Automatic on push to `develop` (testing) or `main` (production).  
See [iu-alumni-infra](https://github.com/iu-alumni/iu-alumni-infra) for the full deployment guide and secrets reference.
