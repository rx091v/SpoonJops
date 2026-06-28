# Database

Phase 2 establishes the PostgreSQL schema, SQLAlchemy models, and Alembic migrations.

## Domains

- Users, settings, API keys
- Companies, jobs, recruiters, contacts
- Applications, events, answers, automation logs
- Resume versions, cover letters, messages, follow-ups
- Skills, job skills, match scoring

## Migrations

Run migrations from the backend service context:

```powershell
docker compose run --rm backend alembic -c backend/alembic.ini upgrade head
```

Generate future revisions after model changes:

```powershell
docker compose run --rm backend alembic -c backend/alembic.ini revision --autogenerate -m "change description"
```
