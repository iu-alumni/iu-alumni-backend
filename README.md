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
SQLALCHEMY_DATABASE_URL=postgresql://user:password@localhost:5432/dbname
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
