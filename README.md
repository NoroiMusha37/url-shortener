# URL Shortener

URL shortener API designed to create compact links, track analytics, and manage redirections seamlessly.

---

## 🚀 Live Deployment

The API is deployed on Render. You can access the live service and its documentation below:

- **Live Application**: [https://url-shortener-514e.onrender.com](https://url-shortener-514e.onrender.com)
- **Swagger Documentation**: [https://url-shortener-514e.onrender.com/docs](https://url-shortener-514e.onrender.com/docs)
- **ReDoc Documentation**: [https://url-shortener-514e.onrender.com/redoc](https://url-shortener-514e.onrender.com/redoc)

You can use already created admin account:
 - **username**: admin
 - **password**: admin

Or register your own non-admin account

---

## ✨ Features

- **Link Shortening**: Convert long URLs into compact, shareable links.
- **Authentication**: JWT-based user authentication.
- **Analytics & Tracking**: Track top referrers and geographical locations using `ip-api.com`.
- **High Performance**: Asynchronous database operations using `asyncpg` and caching via Redis.
- **Rate Limiting**: Built-in rate limiting to prevent abuse.
- **Structured Logging**: Comprehensive and structured logging configured with `structlog`.
- **Containerized**: Fully Dockerized for easy local development and deployment.

---

## 🛠 Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with asyncpg and SQLAlchemy 2.0
- **Migrations**: Alembic
- **Caching & Rate Limiting**: Redis
- **Package Management**: uv
- **Background Tasks**: ARQ / Celery (Branch-specific)

---

## ⏱️ Scheduled Tasks & Branches

This repository contains dedicated branches that implement a scheduled background task responsible for cleaning up and deleting expired short links. 

- **[`celery`](https://github.com/NoroiMusha37/url-shortener/tree/celery) branch**: Implements the scheduled task using Celery.
- **[`arq`](https://github.com/NoroiMusha37/url-shortener/tree/arq) branch**: Implements the scheduled task using ARQ, leveraging Redis.

> Currently, neither of these background task implementations are active in the live production deployment. The project is hosted on Render's free tier, which restricts running persistent, continuous background workers alongside web services. Therefore, the background task implementations are kept in separate branches for demonstration and local usage.

---

## ⚙️ Prerequisites

To run this project locally, you will need:
- Docker
- Python 3.13+ (if running locally without Docker)
- uv

---

## 🔧 Environment Variables

Create a `.env` file in the root directory based on the configuration required in `app/config.py`. 

```env
# Database configuration for local Docker setup
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=url_shortener

# Application configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/url_shortener
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your_super_secret_jwt_key_here
```

---

## 🐳 Running with Docker

The easiest way to get the application running alongside its dependencies (PostgreSQL and Redis) is via Docker Compose.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NoroiMusha37/url-shortener.git
   cd url-shortener
   ```

2. **Start the services:**
   ```bash
   docker compose up --build
   ```

3. **Run Database Migrations:**
   Once the database container is healthy, apply the Alembic migrations to set up your tables:
   ```bash
   docker compose exec app uv run alembic upgrade head
   ```

The API will now be available at `http://localhost:8000`.

---

## 🧪 Testing

The project uses `pytest` and `pytest-asyncio` for testing.

To run the test suite locally:
```bash
uv run pytest
```
**Note**: Services should be active before running the tests.

*(Ensure your testing environment variables and test database are properly configured before running tests).*

---

## 🔄 CI/CD Pipeline

This project uses **GitHub Actions** for Continuous Integration and Continuous Deployment.

- **Testing (`test` job)**: On every push and pull request to the `main` branch, the pipeline spins up temporary PostgreSQL and Redis containers, installs dependencies using `uv`, and runs the `pytest` test suite to ensure code health.
- **Deployment (`deploy` job)**: If the tests pass and the event is a push to the `main` branch, the pipeline automatically triggers a deployment to Render via a secure Deploy Hook.

---

## 📁 Project Structure

```text
├── app/
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Environment variables & Pydantic settings
│   ├── database.py        # SQLAlchemy engine and session management
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic schemas for requests/responses
│   ├── routers/           # API route definitions (auth, links)
│   ├── repositories/      # Database interaction layer
│   ├── ip_api_client.py   # Client for fetching geolocation data
│   ├── worker.py          # ARQ worker configuration
│   └── ...
├── migrations/            # Alembic migration scripts
├── tests/                 # Pytest test suite
├── alembic.ini            # Alembic configuration
├── docker-compose.yml     # Docker services setup
├── Dockerfile             # Docker image definition
├── pyproject.toml         # Project metadata and dependencies
└── uv.lock                # Locked dependency tree
```
