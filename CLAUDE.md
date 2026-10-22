# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

UN-DICAM (DIC Tool): Digital Image Correlation for tensile tests on specimens ("probetas"). FastAPI + Celery + Redis + PostgreSQL backend, Expo / React Native frontend. Code, comments, identifiers in the DIC domain, and user-facing messages are in Spanish — keep that convention.

## Commands

Backend (run from `backend/` so `app.` imports resolve; Python deps live in the root `requirements.txt`, `backend/requirements.txt` just includes it):

```sh
cd backend
pip install -r ../requirements.txt
uvicorn app.main:app --reload                      # API at :8000, Swagger at /docs
celery -A app.Core.celery_app.celery_app worker --loglevel=info
pytest tests -v --tb=short                         # all tests
pytest tests/test_strain.py::test_name -v          # single test
```

Full stack via Docker (backend, worker, redis, postgres; `backend/app` and `storage/` are bind-mounted, uvicorn reloads):

```sh
cp .env.example .env
docker compose up --build
```

Frontend (pnpm is enforced by a `preinstall` hook):

```sh
cd frontend
pnpm install
pnpm start        # or pnpm android / ios / web
```

The frontend reads `EXPO_PUBLIC_API_URL` (default `http://localhost:8000/api/v1`); on a physical device point it at the host's LAN IP.

No linter or formatter is configured.

## Architecture

### Backend (`backend/app`)

Layering: `api/v1/routes/*` (thin FastAPI routers, mounted under `/api/v1` in `api/v1/router.py`) → `services/*` (business logic, raise `*ServiceError` subclasses that routes map to HTTP errors) → `db/models.py` (SQLAlchemy) and `dic/*` (pure numerical DIC code). `schemas/*` hold the Pydantic request/response models.

- `Core/` (capital C) holds `config.py` (pydantic-settings, reads `.env`), `security.py` (password hashing) and `celery_app.py`.
- DB schema is created with `Base.metadata.create_all` (`db/init_db.py`) — there are no migrations; model changes on an existing Postgres volume need a manual drop/alter (e.g. the `filas`/`columnas` columns on `tracking_meshes`).
- `SpecimenConfig` and `TrackingMesh` are keyed by `project_id` (one per project).
- Auth (`/auth/register`, `/auth/login`, PBKDF2) exists but issues no token; no endpoint is protected yet.

**Analysis flow** (the core of the app, spans frontend screens → routes → worker):
1. Project created → specimen calibrated (`/specimen`, px↔mm via `dic/probeta.py`) → tracking mesh built from a user-drawn polygon (`/tracking/mesh`). The mesh is a `filas × columnas` grid (default 3×3, 2–20 each, chosen in `MeshScreen`), nodes stored **row-major** in `TrackingMesh.nodos`.
2. `POST /analysis/start` validates both exist, inserts an `Analysis` row whose id doubles as the Celery `task_id`, and enqueues `workers/tasks.process_full_analysis` (params: `subset_size` default 32, `search_range` default 20, `frame_inicio`/`frame_fin`).
3. The worker opens the video source via `DeviceService.open_capture_for_source_id` (numeric id = camera, otherwise a file path), and compares every frame against the **first (reference) frame** with `dic/pipeline.procesar_par_frames`: ZNCC correlation (Numba) + LSQ subpixel refinement (`correlation.py`, `displacement.py`) → strain per grid cell, `(filas-1) × (columnas-1)` cells (`strain.calcular_deformaciones`). Displacement is reported from the central node (`ResultadoFrame.nodo_centro`). Frames where tracking raises `ValueError` are skipped. Results accumulate in `dic/analisis.Analisis`; progress is reported via `update_state(state="PROGRESS", meta={...})`.
4. Output: strain maps (`dic/mapas.py`) written to `storage/analyses/<id>/` (served at `/storage` by `StaticFiles`) and a `Result` row with JSON curves. `/analysis/status/{id}` reads Celery state; `/analysis/results/{id}` reads the DB.
- Load (`carga_n`) is read per frame by OCR (`dic/ocr.extract_load_value`, pytesseract) when the specimen has a `roi_carga`; otherwise, or when OCR fails, it falls back to `CARGA_N_PLACEHOLDER = 0.0`. The Setup screen currently always sends `roi_carga: null`, so in practice load and stress are 0.

Gotchas:
- Node distribution over the polygon mask is implemented twice: `services/tracking.TrackingService._distribute_nodes` (used by the API) and `dic/rastreo.Rastreo._distribuir_nodos` (library code). Keep them in sync when changing mesh logic.
- Anything that indexes nodes (strain cells, central node) must take `filas`/`columnas` into account — don't hardcode 9 nodes.
- `plan.md` / `todo.md` (Spanish) track phases and pending work; check them for context on planned features.

### Tests

`tests/conftest.py` sets env vars before importing the app: SQLite in-memory DB, in-memory Celery broker, and `task_always_eager=True`, so tasks run synchronously in-process. No Postgres/Redis needed for tests. `test_ocr.py` skips its real-Tesseract test when the binary isn't installed (the Docker image includes it).

### Frontend (`frontend/src`)

- `api/client.js` `apiRequest` is the single fetch wrapper (JSON, maps errors to `ApiError` / `NotFoundError` using the backend's `detail`); per-domain modules in `api/` wrap it — add new endpoints there.
- Navigation: native-stack in `navigation/AppNavigator.js`, route names in `navigation/routes.js`. Each screen lives in `screens/<name>/` with an `index.js` re-export.
- Shared styles in `styles/theme.js`.
