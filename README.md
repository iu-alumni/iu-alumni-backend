# IU Alumni — Backend

FastAPI service providing REST API and Telegram bot logic for the IU Alumni platform.

## Local Development

```bash
cp .env.example .env  # fill in values
docker compose up
```

API available at `http://localhost:8080`. Docs at `http://localhost:8080/docs`.

## Deployment

Automatic on push to `develop` (testing) or `main` (production).  
See [iu-alumni-infra](../iu-alumni-infra/README.md) for full deployment guide and secrets reference.
