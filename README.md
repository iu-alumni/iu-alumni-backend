# IU Alumni Backend

A FastAPI-based backend service for the IU Alumni platform.

## Prerequisites

- Python 3.8+
- PostgreSQL

## Setup

1. Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
POSTGRES_DB=your-database-name
POSTGRES_USER=your-postgres-user
POSTGRES_PASSWORD=your-postgres-password
SQLALCHEMY_DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key
ADMIN_EMAIL=example@example.com
ADMIN_PASSWORD=example1234
MAIL_USERNAME=mail@example.com
MAIL_PASSWORD=example-password
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM=noreply@innopolis.university
MAIL_FROM_NAME=IU Alumni Platform
EMAIL_HASH_SECRET=your-email-hash-secret
NOTIFICATION_BOT_URL=your-notification-bot-url
ENVIRONMENT=DEV
```

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation can be accessed at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
