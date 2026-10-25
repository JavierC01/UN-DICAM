# CLAUDE.md

Guía para agentes de codificación (Claude Code, OpenCode) que trabajan en este repositorio.
Los puntos marcados **[DECIDIR]** son decisiones abiertas del autor: preguntar antes de asumirlas.

## 1. Producto

UN-DICAM es una herramienta **open source** de correlación digital de imágenes (DIC) 2D, con una sola cámara, para caracterizar materiales y elementos de construcción como alternativa o complemento a los ensayos convencionales:

- Probetas de madera y concreto.
- Conexiones metálicas no rectangulares.
- Vigas CLT y CLBT.
- Núcleos de vigas y columnas.

Dos usos: ensayos de laboratorio y sustento académico para la Digital Twins Engineering Conference 2027. Cualquier persona debe poder instalarla.

**Alcance funcional**

- **Ensayos:** tracción, compresión, flexión, cortante/conexiones y momento en pórticos.
- **Geometría:** arbitraria. Nunca asumir probeta rectangular ni grilla completa de nodos.
- **Video:** archivo subido, grabación desde el celular con la app y cámara en vivo en el PC.
- **Carga:** importar el archivo exportado por la máquina (prioridad) y OCR del video para máquinas sin exportación.
- **Salidas:** mapas de deformación sobre la imagen, curvas carga–desplazamiento y esfuerzo–deformación, módulo de elasticidad y otras propiedades, exportación CSV/PDF/JPG.

Código del dominio DIC, comentarios y mensajes al usuario están en **español**. Mantener esa convención.

## 2. Principios no negociables

1. **Rigor científico.** Nunca usar valores placeholder (como `0.0`) que parezcan datos. Si falta un dato: `null`/`NaN` y una advertencia en el resultado.
2. **Reproducibilidad.** Cada análisis guarda parámetros (subset, search range, step), calibración, método de lectura de carga, hash del video y versión/commit del software.
3. **Geometría arbitraria.** Los nodos solo se ubican donde el subset completo cae dentro del objeto. La deformación no depende de una grilla rectangular. Los nodos inválidos se marcan; no se fuerzan al borde.
4. **Unidades explícitas** (px, mm, N, MPa). La conversión px↔mm vive solo en `dic/probeta.py`.
5. **Limitación 2D documentada.** Una cámara, objeto en plano perpendicular al eje óptico; el movimiento fuera del plano introduce error. No prometer medición 3D.
6. **Open source real.** Se instala con `docker compose up` siguiendo el README, sin secretos en el repo, con licencia explícita **[DECIDIR: licencia]**.

## 3. Comandos

Backend (ejecutar desde `backend/` para que resuelvan los imports `app.`; las dependencias están en el `requirements.txt` de la raíz y `backend/requirements.txt` solo lo incluye):

```sh
cd backend
pip install -r ../requirements.txt
uvicorn app.main:app --reload                      # API en :8000, Swagger en /docs
celery -A app.Core.celery_app.celery_app worker --loglevel=info
pytest tests -v --tb=short                         # todos los tests
pytest tests/test_strain.py::test_name -v          # un test
```

Stack completo con Docker (backend, worker, redis, postgres; `backend/app` y `storage/` están montados y uvicorn recarga):

```sh
cp .env.example .env
docker compose up --build
```

Frontend (**pnpm obligatorio**, forzado por un hook `preinstall`; no usar `npm` ni `npx`, usar `pnpm exec`):

```sh
cd frontend
pnpm install
pnpm start        # o pnpm android / ios / web
```

El frontend lee `EXPO_PUBLIC_API_URL` (por defecto `http://localhost:8000/api/v1`); en un dispositivo físico apuntarlo a la IP LAN del host.

No hay linter ni formateador configurado.

## 4. Arquitectura actual del backend (`backend/app`)

Capas: `api/v1/routes/*` (routers FastAPI delgados, montados bajo `/api/v1` en `api/v1/router.py`) → `services/*` (lógica de negocio; lanzan subclases de `*ServiceError` que las rutas traducen a HTTP) → `db/models.py` (SQLAlchemy) y `dic/*` (código numérico DIC puro). `schemas/*` contiene los modelos Pydantic.

- `Core/` (con C mayúscula): `config.py` (pydantic-settings, lee `.env`), `security.py` (hash de contraseñas) y `celery_app.py`.
- El esquema se crea con `Base.metadata.create_all` (`db/init_db.py`). **No hay migraciones**: cambiar un modelo sobre un volumen de Postgres existente exige `ALTER`/borrado manual.
- `SpecimenConfig` y `TrackingMesh` están indexados por `project_id` (uno por proyecto).
- Auth (`/auth/register`, `/auth/login`, PBKDF2) existe pero **no emite token** y ningún endpoint está protegido.

**Flujo de análisis** (pantallas → rutas → worker):

1. Proyecto → calibración de probeta (`/specimen`, px↔mm vía `dic/probeta.py`) → malla de rastreo desde un polígono dibujado (`/tracking/mesh`). La malla es una grilla `filas × columnas` (por defecto 3×3, 2–20 cada una, elegida en `MeshScreen`), con nodos guardados **por filas** en `TrackingMesh.nodos`.
2. `POST /analysis/start` valida que existan calibración y malla, inserta una fila `Analysis` cuyo id es también el `task_id` de Celery y encola `workers/tasks.process_full_analysis` (`subset_size` 32, `search_range` 20, `frame_inicio`/`frame_fin`).
3. El worker abre la fuente con `DeviceService.open_capture_for_source_id` (id numérico = cámara; si no, ruta de archivo) y compara cada frame contra el **primer frame (referencia)** con `dic/pipeline.procesar_par_frames`: ZNCC con Numba + refinamiento subpíxel por mínimos cuadrados (`correlation.py`, `displacement.py`) → deformación por celda `(filas-1) × (columnas-1)` (`strain.calcular_deformaciones`). El desplazamiento se reporta desde el nodo central (`ResultadoFrame.nodo_centro`). Los frames donde el rastreo lanza `ValueError` se omiten.
4. Salida: mapas en `storage/analyses/<id>/` (servidos en `/storage`) y una fila `Result` con curvas JSON.
5. Carga (`carga_n`): OCR por frame (`dic/ocr.extract_load_value`, pytesseract) si la calibración tiene `roi_carga`; si no hay ROI o el OCR falla, cae en `CARGA_N_PLACEHOLDER = 0.0`. **Esto viola el principio 1 y está en el plan para corregirse.** La pantalla Setup hoy envía siempre `roi_carga: null`, así que en la práctica carga y esfuerzo son 0.

**Cuidados al editar**

- La distribución de nodos está implementada **dos veces**: `services/tracking.TrackingService._distribute_nodes` (la usa la API) y `dic/rastreo.Rastreo._distribuir_nodos` (biblioteca). Mantenerlas sincronizadas o, mejor, eliminar una.
- Todo lo que indexe nodos (celdas de deformación, nodo central) debe usar `filas`/`columnas`; no fijar 9 nodos.
- `DeviceService` usa `cv2.CAP_DSHOW` para cámaras, que solo existe en Windows. En Linux/Docker no funciona; los archivos usan `CAP_ANY`.
- `source_id` de tipo archivo acepta hoy cualquier ruta del servidor (riesgo de seguridad pendiente).
- `plan.md` y `todo.md` registran fases y pendientes; consultarlos antes de empezar una tarea.

### Tests

`tests/conftest.py` fija variables de entorno antes de importar la app: SQLite en memoria, broker de Celery en memoria y `task_always_eager=True`, de modo que las tareas corren de forma síncrona. No hace falta Postgres ni Redis. `test_ocr.py` omite el test real de Tesseract si el binario no está (la imagen Docker lo incluye).

## 5. Arquitectura objetivo del backend

- **Estrategia por tipo de ensayo** (`dic/ensayos/`): interfaz común que, para tracción, compresión, flexión, cortante y pórtico, define cómo se calcula el esfuerzo, qué mide el extensómetro virtual y cómo se obtiene el módulo. Un ensayo nuevo no debe tocar el pipeline DIC.
- **Extensómetros virtuales:** longitud de calibración entre dos puntos (tracción/compresión), deflexión (flexión), deslizamiento relativo (conexiones), rotación (pórticos).
- **Fuentes de carga** (`cargas/`): importador CSV/XLSX con mapeo de columnas y unidades; OCR con ROI que cuenta y reporta fallos; sincronización temporal con los frames (offset, evento de inicio, interpolación a los tiempos de frame).
- **Módulo de elasticidad:** ajuste lineal sobre un rango que el usuario elige según la norma aplicable; se reporta el rango y el R². Nunca elegir el rango en silencio **[DECIDIR: normas por material]**.
- **Geometría arbitraria:** nodos válidos dentro de una máscara erosionada por la mitad del subset; deformación por triangulación (elementos de deformación constante) o ventana local; mapas dibujados sobre el primer frame.
- **Subida de video:** endpoint con límite de tamaño y validación de extensión; el `source_id` de archivo apunta a `storage/uploads/` y nunca a rutas arbitrarias.
- **Datos:** Alembic para migraciones; `owner_id` en `Project`; JWT en todos los endpoints.

## 6. Frontend (`frontend/src`) y diseño atómico

### Estado actual

- `api/client.js`: `apiRequest` es el único wrapper de `fetch` (JSON; traduce errores a `ApiError` / `NotFoundError` con el `detail` del backend). Un módulo por dominio en `api/`; los endpoints nuevos se agregan ahí.
- Navegación: native-stack en `navigation/AppNavigator.js`; nombres de ruta en `navigation/routes.js`. Cada pantalla vive en `screens/<nombre>/` con un `index.js` que la reexporta.
- Estilos compartidos en `styles/theme.js`.

### Estructura objetivo (Atomic Design)

```
frontend/src/
  components/
    atoms/        Button, TextField, Typography, Label, Icon, Badge, Spinner, Divider
    molecules/    FormField, SegmentedControl, MetricCard, ProgressBar, InlineMessage,
                  KeyValueRow, ImageWithCaption
    organisms/    LoginForm, RegisterForm, ProjectList, SpecimenForm, VideoSourcePicker,
                  FrameAnnotator, MeshParametersPanel, AnalysisProgressPanel,
                  ResultsSummary, CurveChart, StrainMapGallery, ExportPanel
    templates/    AuthTemplate, ScreenTemplate, WizardTemplate
  screens/        páginas: Login, Registro, Proyectos, Setup, Captura, Malla,
                  Resultados, Reportes, Manual
  hooks/          useAnalysisStatus, useFirstFrame, ...
  api/  navigation/  styles/
```

Cada componente vive en su carpeta (`Button/Button.js`, `Button/index.js`, `Button/Button.test.js`), igual que las pantallas.

**Reglas**

1. **Dirección de imports:** `atoms ← molecules ← organisms ← templates ← screens`. Un nivel solo importa de los inferiores, nunca de los superiores ni de su mismo nivel (salvo molecules entre sí si no hay ciclo y se justifica).
2. **Átomos y moléculas son puros:** reciben props, no tienen estado de negocio, no llaman a `api/` ni a `navigation`.
3. **Organismos** pueden tener estado local de UI y exponen callbacks (`onSubmit`, `onChange`); no llaman a `api/`.
4. **Solo las pantallas (páginas)** llaman a `api/*`, usan `navigation` y hooks de datos, y pasan datos y callbacks hacia abajo.
5. **Templates** solo resuelven layout (encabezado, área desplazable, barra de acción, indicador de pasos); no contienen datos.
6. **Tokens de diseño:** `styles/theme.js` define `colors`, `spacing`, `typography` y `radii`. Los componentes usan solo tokens; sin colores ni tamaños literales.
7. **Accesibilidad:** `accessibilityLabel` en átomos interactivos, áreas táctiles de al menos 44 pt, contraste suficiente.
8. **Textos de usuario** en un solo lugar (`src/i18n/es.js`) para facilitar una futura traducción **[DECIDIR: ¿i18n en la app?]**.
9. **Dependencias:** no agregar librerías de UI. Antes de añadir una de gráficas, evaluar `react-native-svg` y dibujar `CurveChart` propio. Cualquier dependencia nueva se instala con pnpm y se justifica.

**Organismo clave: `FrameAnnotator`.** Muestra un frame y permite marcar sobre él en distintos modos:

- `line` — dos toques: mide `long_calibracion_px`.
- `rect` — rectángulo: ROI de la carga para el OCR.
- `polygon` — vértices: región de interés y malla.

Un solo organismo reemplaza tres pendientes del `todo.md` (calibración medida, ROI de carga y polígono de malla). Debe aceptar frames de cualquier resolución y devolver coordenadas en píxeles del frame original.

**Migración:** no reescribir todo de golpe. Una pantalla por PR, empezando por Login (la más pequeña), y la pantalla debe seguir funcionando al terminar. Primero tokens + átomos + moléculas; después organismos; por último templates.

**Tests de frontend:** átomos y moléculas con tests de render (jest-expo + Testing Library), instalados con pnpm. Hoy no hay ningún test de frontend.

## 7. Reglas de trabajo para el agente

- Cambios pequeños y verificables; correr `pytest` antes de dar una tarea por terminada.
- No duplicar lógica: antes de construir sobre `dic/` vs `services/` (dispositivos, rastreo, análisis), eliminar la duplicación existente.
- No commitear `__pycache__`, `.expo/`, `.env`, videos de prueba ni el contenido de `storage/`.
- Toda función DIC nueva lleva un test con datos sintéticos de desplazamiento conocido.
- No marcar una tarea como hecha si queda un `NotImplementedError`, un stub o un placeholder en su camino.
- **Preguntar antes de:** cambiar el algoritmo de correlación, el formato de resultados, el esquema de la base de datos, o agregar dependencias (revisar su licencia).
- Cambios de esquema: con migración Alembic una vez exista; mientras tanto, documentar el `ALTER` necesario.

## 8. Validación (requisito para publicar)

- Carpeta `validation/` con scripts reproducibles.
- Imágenes sintéticas con desplazamiento y deformación conocidos (traslación rígida, estiramiento uniforme, gradiente): reportar error medio y desviación.
- Comparación contra extensómetro, LVDT o galga en ensayos reales.
- Documentar la resolución de deformación alcanzada según la calidad del patrón speckle.

## 9. Definición de "terminado"

- Los tests pasan y hay tests nuevos para lo agregado.
- Sin placeholders ni stubs en el flujo afectado.
- Migración incluida si cambió el esquema.
- Componentes de UI colocados en su nivel atómico correcto.
- README, `todo.md` y `plan.md` actualizados.
