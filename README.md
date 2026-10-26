# UN-DICAM

**English summary.** UN-DICAM is an open-source 2D Digital Image Correlation (DIC) tool (single camera) for characterizing construction materials and structural elements: timber and concrete specimens, non-rectangular steel connections, CLT/CLBT beams, and beam/column cores. It supports tension, compression, bending, shear/connection and frame-moment tests. Status: early development; validate results against reference measurements before using them for engineering decisions.

---

UN-DICAM es una herramienta **open source** de correlación digital de imágenes (DIC) 2D, con una sola cámara, para caracterizar materiales y elementos de construcción como alternativa o complemento a los ensayos convencionales:

- Probetas de madera y concreto.
- Conexiones metálicas no rectangulares.
- Vigas CLT y CLBT.
- Núcleos de vigas y columnas.

Está pensada para ensayos de tracción, compresión, flexión, cortante/conexiones y momento en pórticos, y también como apoyo académico a la validación del DIC como metodología alterna.

> **Estado:** en desarrollo temprano. El flujo completo funciona (video → calibración → carga → malla → análisis → propiedades → exportación), pero la validación científica contra extensómetro/LVDT aún no está hecha. No uses los resultados para decisiones de ingeniería sin contrastarlos con una medición de referencia. Consulta [plan.md](plan.md) y [todo.md](todo.md).

## Qué hace hoy

1. Registro, inicio de sesión con JWT (todos los endpoints exigen token) y gestión de proyectos.
2. Video: subida de archivo desde el PC o el celular, grabación con la cámara del celular, o cámara conectada al servidor (Windows `CAP_DSHOW`, Linux `CAP_V4L2`).
3. Calibración píxeles ↔ milímetros midiendo una distancia conocida con dos toques sobre el primer frame.
4. Tipo de ensayo: tracción, compresión, flexión, cortante/conexiones o momento en pórtico, cada uno con su extensómetro virtual.
5. Carga: archivo CSV/XLSX de la máquina (mapeo de columnas y unidades, sincronización con offset o umbral de carga e interpolación a los tiempos de frame) u OCR sobre una región dibujada en el frame. Los puntos sin carga quedan nulos y se reportan; nunca valen 0.
6. Geometría arbitraria: el polígono puede ser cualquier forma (L, entalla, hueso de perro). Solo son válidos los nodos cuyo subset completo cae dentro; la deformación se calcula por triangulación de Delaunay con elementos de deformación constante (CST).
7. Análisis asíncrono: ZNCC con refinamiento subpíxel, mapas εxx, εyy, εxy dibujados sobre el primer frame, curvas carga–desplazamiento, esfuerzo–deformación y la curva propia del ensayo.
8. Propiedad del ensayo (módulo de elasticidad, rigidez a flexión, módulo de deslizamiento, rigidez rotacional) por ajuste lineal en el rango que el usuario elige; se reportan rango, pendiente y R².
9. Exportación CSV, PDF y JPG con metadatos de reproducibilidad (parámetros, calibración, método de carga, hash del video, versión y commit), e historial de análisis por proyecto.

## Limitaciones conocidas

- **DIC 2D con una sola cámara:** el objeto debe estar en un plano perpendicular al eje óptico. El movimiento fuera del plano introduce error.
- La calidad depende del patrón speckle y de la iluminación.
- Sin fuente de carga configurada, carga y esfuerzo quedan nulos (con advertencia en el resultado).
- La referencia es siempre el primer frame: deformaciones grandes pueden perder nodos (falta el rastreo incremental).
- Las cámaras en vivo necesitan el backend nativo (Windows o Linux con V4L2); dentro de Docker no hay acceso a cámaras USB, así que usa un video subido o grabado con el celular.
- Todos los usuarios ven todos los proyectos (falta `owner_id`), los mapas en `/storage` son públicos (URL con UUID) y las descargas aceptan el token como parámetro `?token=`: **no expongas el backend a internet**.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) con Docker Compose.
- Node.js y [pnpm](https://pnpm.io/) para el frontend (el proyecto fuerza pnpm; no uses `npm` ni `npx`).
- Para probar en un celular: la app Expo Go, o un emulador de Android/iOS.

## Inicio rápido

### 1. Backend (Docker)

```sh
cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
# Edita SECRET_KEY en .env (obligatoria, mínimo 32 caracteres):
python -c "import secrets; print(secrets.token_hex(32))"
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

### Flujo en la app

Proyectos → **Nuevo análisis** → Captura (subir o grabar el video) → Configuración (calibración, tipo de ensayo y fuente de carga) → Malla (polígono y puntos del extensómetro) → Resultados (curvas, mapas y ajuste de la propiedad) → Reportes (CSV/PDF/JPG). El manual dentro de la app explica cada paso.

Los videos se suben con `POST /api/v1/devices/upload` (extensiones `.mp4 .mov .avi .mkv .m4v .webm .3gp`, máximo `MAX_UPLOAD_MB`, 500 MB por defecto) y quedan en `storage/uploads/`. El `source_id` de un archivo es el nombre que devuelve la subida; el backend no abre rutas arbitrarias del servidor.

### Cambios de esquema (sin migraciones todavía)

`create_all` crea tablas nuevas (`machine_loads`) pero no agrega columnas a las existentes. Si tu volumen de Postgres es anterior a la Fase 7, ejecuta una vez (`docker compose exec db psql -U undicam undicam`):

```sql
ALTER TABLE specimen_config ADD COLUMN IF NOT EXISTS tipo_ensayo VARCHAR(30) NOT NULL DEFAULT 'traccion';
ALTER TABLE specimen_config ADD COLUMN IF NOT EXISTS parametros_ensayo JSON;
ALTER TABLE specimen_config ADD COLUMN IF NOT EXISTS fuente_carga VARCHAR(20) NOT NULL DEFAULT 'ninguna';
ALTER TABLE tracking_meshes ADD COLUMN IF NOT EXISTS validos JSON;
ALTER TABLE tracking_meshes ADD COLUMN IF NOT EXISTS subset_size INTEGER;
ALTER TABLE tracking_meshes ADD COLUMN IF NOT EXISTS puntos_ensayo JSON;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
DROP TABLE IF EXISTS image_pairs;  -- modelo eliminado, nunca se usó
```

O bien borra el volumen (`docker compose down -v`), perdiendo los datos. Los resultados guardados antes de este cambio siguen leyéndose, pero no tienen curva del ensayo ni metadatos.

## Backend sin Docker (opcional)

Requiere Python, PostgreSQL y Redis disponibles, y las variables de `.env` apuntando a ellos.

```sh
cd backend
python -m venv venv
source venv/bin/activate              # Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r ../requirements.txt
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")   # o ponla en .env
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
  dic/             código numérico DIC (correlación, desplazamiento, malla, deformación CST, mapas, OCR, exportación)
  dic/ensayos/     estrategia por tipo de ensayo: extensómetro virtual, respuesta y ajuste de la propiedad
  cargas/          importación del archivo de la máquina y sincronización carga ↔ frames
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
