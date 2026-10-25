# UN-DICAM

**English summary.** UN-DICAM is an open-source 2D Digital Image Correlation (DIC) tool (single camera) for characterizing construction materials and structural elements: timber and concrete specimens, non-rectangular steel connections, CLT/CLBT beams, and beam/column cores. It supports tension, compression, bending, shear/connection and frame-moment tests. Status: early development; validate results against reference measurements before using them for engineering decisions.

---

UN-DICAM es una herramienta **open source** de correlación digital de imágenes (DIC) 2D, con una sola cámara, para caracterizar materiales y elementos de construcción como alternativa o complemento a los ensayos convencionales:

- Probetas de madera y concreto.
- Conexiones metálicas no rectangulares.
- Vigas CLT y CLBT.
- Núcleos de vigas y columnas.

Está pensada para ensayos de tracción, compresión, flexión, cortante/conexiones y momento en pórticos, y también como apoyo académico a la validación del DIC como metodología alterna.

> **Estado:** en desarrollo temprano. El flujo básico funciona, pero la carga leída del video, la exportación de resultados y la validación científica aún no están completas. No uses los resultados para decisiones de ingeniería sin contrastarlos con una medición de referencia. Consulta [plan.md](plan.md) y [todo.md](todo.md).

## Qué hace hoy

1. Registro e inicio de sesión de usuarios y gestión de proyectos.
2. Calibración de la probeta (píxeles ↔ milímetros).
3. Carga de un video (por ruta de archivo) o cámara; vista previa del primer frame.
4. Marcado de la región de interés y malla de nodos configurable (`filas × columnas`, 2–20).
5. Análisis asíncrono: correlación ZNCC con refinamiento subpíxel, desplazamientos y deformaciones εxx, εyy, εxy por celda.
6. Estado en tiempo casi real y resumen de métricas.

**En desarrollo:** subida y grabación de video desde el celular, geometrías no rectangulares, importación del archivo de carga de la máquina, módulo de elasticidad, gráficas, y exportación CSV/PDF/JPG.

## Limitaciones conocidas

- **DIC 2D con una sola cámara:** el objeto debe estar en un plano perpendicular al eje óptico. El movimiento fuera del plano introduce error.
- La calidad depende del patrón speckle y de la iluminación.
- La carga y el esfuerzo requieren la lectura de la carga (OCR o archivo de la máquina); mientras no esté configurada, valen 0.
- La exportación (`/export/*`) devuelve 501 (no implementada).
- Las cámaras en vivo solo funcionan en Windows nativo (`CAP_DSHOW`); en Linux/Docker usa un archivo de video.
- Los endpoints aún no exigen autenticación: **no expongas el backend a internet**.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) con Docker Compose.
- Node.js y [pnpm](https://pnpm.io/) para el frontend (el proyecto fuerza pnpm; no uses `npm` ni `npx`).
- Para probar en un celular: la app Expo Go, o un emulador de Android/iOS.

## Inicio rápido

### 1. Backend (Docker)

```sh
cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
docker compose up --build
```

Servicios:

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

Las credenciales de Postgres del `docker-compose.yml` son **solo para desarrollo**; cámbialas antes de cualquier despliegue real.

### 2. Frontend

```sh
cd frontend
pnpm install
pnpm start        # o pnpm android / ios / web
```

El frontend lee la variable `EXPO_PUBLIC_API_URL` (por defecto `http://localhost:8000/api/v1`). En un dispositivo físico, apúntala a la IP de red local de tu computador, por ejemplo:

```sh
EXPO_PUBLIC_API_URL=http://192.168.1.20:8000/api/v1 pnpm start
```

### 3. Crear un usuario de prueba

Desde la pantalla de Registro de la app, o por la API:

```sh
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Usuario Test","email":"test@undicam.com","password":"Test1234!"}'
```

### Video de prueba

Por ahora el video de tipo archivo se indica por **ruta dentro del contenedor del backend**. Coloca el video en la carpeta `storage/` (montada en el contenedor) y usa la ruta `storage/<archivo>`. La subida desde la app está en desarrollo.

## Backend sin Docker (opcional)

Requiere Python, PostgreSQL y Redis disponibles, y las variables de `.env` apuntando a ellos.

```sh
cd backend
python -m venv venv
source venv/bin/activate              # Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r ../requirements.txt
uvicorn app.main:app --reload
# en otra terminal, con el mismo entorno:
celery -A app.Core.celery_app.celery_app worker --loglevel=info
```

## Tests

```sh
cd backend
pytest tests -v --tb=short
```

Los tests usan SQLite en memoria y Celery síncrono: no necesitan Postgres ni Redis. El test real de OCR se omite si Tesseract no está instalado (la imagen Docker sí lo incluye).

## Estructura del repositorio

```
backend/app/
  api/v1/routes/   routers FastAPI (delgados)
  services/        lógica de negocio
  dic/             código numérico DIC (correlación, desplazamiento, deformación, OCR)
  db/              modelos SQLAlchemy
  workers/         tareas Celery
frontend/src/
  components/      diseño atómico: atoms, molecules, organisms, templates
  screens/         páginas
  api/             cliente HTTP por dominio
storage/           videos y mapas generados (no se versiona su contenido)
```

La organización del frontend sigue **diseño atómico**; las reglas están en [CLAUDE.md](CLAUDE.md).

## Contribuir

Antes de empezar una tarea, revisa [plan.md](plan.md) y [todo.md](todo.md). Las reglas de trabajo (idioma, pnpm, tests con datos sintéticos, dirección de imports en el frontend) están en [CLAUDE.md](CLAUDE.md). Un `CONTRIBUTING.md` formal está pendiente.

## Licencia

**[DECIDIR]** Pendiente de definir la licencia. Hasta que se agregue un archivo `LICENSE`, el código no tiene una licencia de uso declarada.

## Agradecimientos y referencias

Pendiente: atribución de código y bibliografía de terceros utilizados (por ejemplo, generadores de patrones speckle y referencias de DIC).
