# Spoon Jops

Production-oriented AI job search automation platform built incrementally from the specification.

## Phase Status

- Phase 1: Project setup, baseline services, Docker Compose, health checks, and documentation.
- Phase 2: Database schema, SQLAlchemy models, and Alembic initial migration.
- Phase 3: Backend APIs.
- Phase 4+: Job discovery, matching, resume generation, browser automation, outreach, dashboard, analytics.

## Stack

- Backend: Python 3.13, FastAPI, SQLAlchemy, Alembic, Pydantic
- Worker: Celery, Redis, APScheduler
- Browser automation: Playwright
- Frontend: React, Vite, Material UI, TanStack Query, React Router, Recharts
- Storage: PostgreSQL, local filesystem, S3-compatible abstraction in later phases
- Deployment: Docker Compose

## Quick Start

1. Copy `.env.example` to `.env` and update secrets.
2. Start the stack:

```powershell
docker compose up --build
```

3. Open:

- API health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

## Validation

```powershell
docker compose run --rm backend pytest
docker compose run --rm frontend npm test -- --run
```

Local Python and Node are not required when using Docker.

## Database Migrations

```powershell
docker compose run --rm backend alembic -c backend/alembic.ini upgrade head
```

## Profile Config

The default demo profile is wired from your resume at `storage/rahul_mathur_resume.pdf` and targets:

- `Lead Software Engineer`
- `Staff Software Engineer`
- `Bengaluru`
- `Remote`
- `10+` years experience

Override the profile through `.env` if you want different titles, locations, or keywords.
