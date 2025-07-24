# IU Alumni Backend

A FastAPI-based backend service for the IU Alumni platform.

## Prerequisites

- Docker
- Docker Compose

## Setup

### 1. Create External Volume

```bash
docker volume create postgres_data
```

### 2. Clone Repository

```bash
git clone https://github.com/iu-alumni/iu-alumni-backend.git
cd iu-alumni-backend
```

### 3. Configure Environment

Create a `.env` file with the following variables:

```bash
# Database
POSTGRES_DB=iu_alumni_db
POSTGRES_USER=alumni_user
POSTGRES_PASSWORD=your-secure-password

# Application
SECRET_KEY=your-secret-key-change-this-in-production
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-admin-password

# Email Configuration
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM=noreply@innopolis.university
MAIL_FROM_NAME=IU Alumni Platform
EMAIL_HASH_SECRET=your-email-hash-secret

# Notifications
NOTIFICATION_BOT_URL=https://your-notification-bot-url.netlify.app/.netlify/functions

# Environment
ENVIRONMENT=DEV  # Set to DEV to enable /docs and /redoc endpoints
```

### 4. Build and Start Services

```bash
# Start core services (database + app)
docker-compose up -d

# Or start all services including scheduler for event notifications
docker-compose --profile scheduler up -d
```

### 5. Install Pre-commit Hooks (for development)

```bash
# Install development dependencies locally
pip install -r requirements-dev.txt

# Install git hooks
pre-commit install --install-hooks
```

## Running the Application

### Start Services

```bash
# Start all services in detached mode
docker-compose --profile scheduler up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Access the API

- API: `http://localhost:8080`
- Swagger Documentation: `http://localhost:8080/docs` (only available when `ENVIRONMENT=DEV`)
- ReDoc Documentation: `http://localhost:8080/redoc` (only available when `ENVIRONMENT=DEV`)

## Development

The application runs with hot-reload enabled. Any changes to the code will automatically restart the server.

To run pre-commit hooks manually:

```bash
pre-commit run --all-files
```
