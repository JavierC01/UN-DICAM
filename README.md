# UN-DICAM

Base de integracion para DIC Tool con FastAPI, Celery, Redis, PostgreSQL y frontend Expo.

## Backend local

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
uvicorn app.main:app --reload
```

## Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Servicios:

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Tests

```powershell
cd backend
pytest tests -v --tb=short
```
