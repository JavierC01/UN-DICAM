# Plan de trabajo — UN-DICAM

Estado al 2026-10-26. Basado en el código de `main` (último commit revisado: `46de069`) más los cambios de la Fase 7.

UN-DICAM es una herramienta **open source** de Correlación Digital de Imágenes (DIC) 2D con una sola cámara, para caracterizar materiales y elementos de construcción: probetas de madera y concreto, conexiones metálicas no rectangulares, vigas CLT y CLBT, y núcleos de vigas y columnas. Soporta ensayos de tracción, compresión, flexión, cortante/conexiones y momento en pórticos, y tiene un objetivo académico: presentar el DIC como metodología alterna a los ensayos convencionales en la Digital Twins Engineering Conference 2027.

El usuario calibra el objeto, sube o graba un video (o usa una cámara en vivo), marca la región de interés, y el backend rastrea una malla de nodos frame a frame para obtener desplazamientos, deformaciones, carga (importada de la máquina o leída por OCR), esfuerzo y propiedades del material.

**Arquitectura:** FastAPI + SQLAlchemy (PostgreSQL) + Celery/Redis en el backend; Expo / React Native en el frontend, organizado con **diseño atómico**; todo orquestado con `docker-compose`.

## Resumen del estado

| Fase | Tema | Estado |
|---|---|---|
| 1 | Infraestructura base | ✅ Completada |
| 2 | Cuentas de usuario y proyectos | 🟡 Casi completa (falta `owner_id`) |
| 3 | Configuración del ensayo (probeta, video, malla) | ✅ Completada |
| 4 | Motor DIC y análisis asíncrono | 🟡 Casi completa (falta rastreo incremental) |
| 5 | Resultados, exportación y reportes | ✅ Completada |
| 6 | Calidad, seguridad, open source y validación | 🟡 Parcial |
| 7 | Geometría arbitraria, tipos de ensayo y carga | ✅ Completada (sin segmentación automática ni normas por material) |
| 8 | Diseño atómico del frontend | 🟡 Iniciada (tokens, `FrameAnnotator`, `CurveChart`, `SegmentedControl`) |

El flujo completo funciona de punta a punta: **login (JWT) → proyecto → video (subido, grabado o cámara) → calibración, tipo de ensayo y fuente de carga → malla en forma arbitraria y extensómetro virtual → análisis → curvas, mapas y propiedad → exportación CSV/PDF/JPG**. Lo que falta es, sobre todo: (a) la validación científica contra extensómetro/LVDT para la conferencia; (b) probar el frontend en dispositivos (las dependencias nuevas no se pudieron instalar en el entorno de desarrollo); (c) proyectos por usuario y migraciones; (d) completar el diseño atómico del frontend.

> Nota: el código del backend referencia "Fase 5" (exportación y OCR). La numeración 1–6 se mantiene para no romper esas referencias; los temas nuevos son las fases 7 y 8.

---

## Fase 1 — Infraestructura base ✅

- `docker-compose.yml` con backend, worker de Celery, Redis y PostgreSQL.
- `Dockerfile` con OpenCV y `tesseract-ocr` instalados.
- Configuración por `.env` ([backend/app/Core/config.py](backend/app/Core/config.py)), CORS, montaje de `/storage` como archivos estáticos.
- Endpoints `/` y `/health`, router versionado `/api/v1`.
- Creación de tablas al arrancar (`init_db` con `create_all`) y espera a la base de datos (`wait_for_db`).
- Suite de tests con pytest (23 pasan, 1 se omite si no hay Tesseract local).
- Archivo `CLAUDE.md` con guía para agentes de codificación.

**Pendiente menor:** migraciones con Alembic (hoy cualquier cambio de modelo exige borrar la base) y limpiar archivos versionados que no deberían estarlo (`__pycache__`, `.expo/`, `backend/package.json`).

## Fase 2 — Cuentas de usuario y proyectos 🟡

**Hecho**
- Registro y login con PBKDF2; el login emite un JWT HS256 (`SECRET_KEY` obligatoria) que exigen todos los endpoints salvo `/auth`.
- Sesión en el frontend (`expo-secure-store`, localStorage en web), cierre de sesión y regreso al login ante un 401.
- CRUD de proyectos con estados `pending`, `in_progress`, `completed`, `failed` y `revoked`.

**Falta**
- **Proyectos por usuario:** `Project` no tiene `owner_id`; todos los usuarios ven todos los proyectos.
- Validaciones de formulario (correo, longitud de contraseña) en el frontend.

## Fase 3 — Configuración del ensayo ✅

- Video: subida desde PC o celular (`POST /devices/upload`, extensión y tamaño validados, archivos solo en `storage/uploads/`), grabación con `expo-camera`, cámaras del servidor con `CAP_DSHOW` (Windows) o `CAP_V4L2` (Linux).
- Flujo Captura → Configuración → Malla: la calibración (línea), la ROI de carga (rectángulo), el polígono y los puntos del extensómetro se marcan sobre el primer frame con `FrameAnnotator`.
- Tipo de ensayo, parámetros y fuente de carga (archivo de la máquina, OCR o ninguna) en Configuración.
- **Falta (menor):** recuperar la malla guardada al volver a la pantalla (`GET /tracking/{project_id}`).

## Fase 4 — Motor DIC y análisis asíncrono 🟡

**Hecho**
- ZNCC con Numba, pico entero y refinamiento subpíxel por mínimos cuadrados; los nodos inválidos o que no se pudieron rastrear en un frame quedan nulos en vez de descartar el frame.
- Deformación CST por triangulación; tarea Celery con estados `running`/`success`/`failed` en el análisis y el proyecto; cancelación marca `revoked`.
- La carga faltante (OCR fallido, frame fuera del registro, sin fuente) queda nula, se cuenta y se advierte; nunca se usa `0.0`.
- WebSocket de progreso eliminado (la app usa sondeo); `step_size` eliminado (el paso lo fija la malla).

**Falta**
- La referencia es siempre el frame inicial; para deformaciones grandes conviene actualizar la referencia (rastreo incremental).

## Fase 5 — Resultados, exportación y reportes ✅

- Resultados: curva del ensayo con ajuste de la propiedad, carga–desplazamiento (x = desplazamiento, y = carga), esfuerzo–deformación (`CurveChart` propio con `react-native-svg`), mapas sobre el primer frame, advertencias y resumen de carga.
- Exportación CSV, PDF y JPG (`dic/export.py`) con metadatos de reproducibilidad; historial `GET /projects/{id}/analyses`; pantalla de Reportes con descargas.

## Fase 6 — Calidad, seguridad, open source y validación 🟡

- **Hecho:** autenticación en todos los endpoints, `source_id` restringido a `storage/uploads/`, límite de tamaño en la subida, tests de rutas (auth, cargas, malla, análisis, export), manual de usuario.
- **Falta:** CORS restringido por defecto; descargas sin token en la URL y `/storage` protegido; tests de frontend (jest-expo no está instalado); prueba real del OCR con Tesseract en Docker.
- **Open source:** archivo `LICENSE` **[DECIDIR]**, README bilingüe, `CONTRIBUTING.md`, integración continua con pytest, atribución a código de terceros.
- **Validación científica:** carpeta `validation/` con imágenes sintéticas de desplazamiento conocido y comparación contra extensómetro/LVDT/galga en ensayos reales; documentar la resolución de deformación y la limitación 2D.

## Fase 7 — Geometría arbitraria, tipos de ensayo y carga ✅

**Geometría arbitraria** (`dic/rastreo.py`, `dic/strain.py`, `dic/mapas.py`)
- Grilla `filas × columnas` sobre la zona válida (máscara erosionada por el subset); los nodos que caen en huecos quedan inválidos (`validos`) y no se rastrean ni se mueven al borde.
- Deformación por triangulación de Delaunay de los nodos válidos con elementos CST; se descartan triángulos que crucen fuera de la forma; medias ponderadas por área. La versión de grilla pone `NaN` en celdas con esquinas inválidas.
- Nodo central = nodo válido más cercano al centroide del polígono. Mapas dibujados sobre el primer frame.
- Una sola implementación de la distribución de nodos; duplicados entre `dic/` y `services/` eliminados.
- Pendiente opcional: segmentación automática de la forma.

**Tipos de ensayo** (`dic/ensayos/`, estrategia por tipo)
- Interfaz `Ensayo`: puntos a marcar, extensómetro virtual (`medir`), respuesta a partir de la carga y propiedad (pendiente).
- Tracción y compresión (deformación entre dos puntos, esfuerzo F/A → módulo de elasticidad), flexión (deflexión relativa a los apoyos → rigidez), cortante/conexiones (deslizamiento relativo en el eje de carga → módulo de deslizamiento), pórtico (rotación y momento F·brazo → rigidez rotacional).
- Ajuste lineal en el rango que elige el usuario (en x o como fracción de la respuesta máxima), con R² y rango reportados. Las normas por material siguen **[DECIDIR]**.

**Carga** (`cargas/`)
- Importador CSV/XLSX con mapeo de columnas y unidades; sincronización por offset y evento de inicio (umbral de carga); interpolación a los tiempos de frame; frames fuera del registro quedan nulos y se cuentan.
- OCR con ROI dibujada en la UI; los fallos se descartan y se cuentan.

**Reproducibilidad:** cada resultado guarda parámetros, malla, calibración, método y archivo de carga (con sha256), hash del video, versión y commit (`GIT_COMMIT`), y advertencias.

## Fase 8 — Diseño atómico del frontend 🟡

Objetivo: una UI consistente, reutilizable y testeable. Las reglas completas (dirección de imports, qué puede llamar a la API, tokens) están en [CLAUDE.md](CLAUDE.md).

| Nivel | Contenido |
|---|---|
| **Tokens** (`styles/theme.js`) | colores, espaciado, tipografía, radios |
| **Átomos** | Button, TextField, Typography, Label, Icon, Badge, Spinner, Divider |
| **Moléculas** | FormField, SegmentedControl, MetricCard, ProgressBar, InlineMessage, KeyValueRow, ImageWithCaption |
| **Organismos** | LoginForm, RegisterForm, ProjectList, SpecimenForm, VideoSourcePicker, **FrameAnnotator**, MeshParametersPanel, AnalysisProgressPanel, ResultsSummary, CurveChart, StrainMapGallery, ExportPanel |
| **Templates** | AuthTemplate, ScreenTemplate, WizardTemplate (pasos Setup → Captura → Malla → Resultados) |
| **Páginas** | las pantallas existentes, que solo orquestan datos, API y navegación |

**`FrameAnnotator`** es el organismo clave: un solo componente con modos `line` (calibración), `rect` (ROI de carga) y `polygon` (malla), que resuelve tres pendientes de la Fase 3.

**Estrategia de migración:** una pantalla por PR sin romper el flujo actual. Orden: tokens → átomos → moléculas → migrar Login → Registro → Proyectos → organismos de captura/malla (`FrameAnnotator`) → Resultados y Reportes → templates. Sin librerías de UI externas; evaluar `react-native-svg` y gráficas propias antes de añadir una librería de gráficas (todo con pnpm).

---

## Orden recomendado

1. **Estabilizar la base:** limpiar el repo, eliminar duplicados, `LICENSE`, Alembic, JWT y proyectos por usuario.
2. **Cimientos de UI:** tokens, átomos y moléculas, y el organismo `FrameAnnotator` (desbloquea calibración medida, ROI de carga y polígono).
3. **Fuente de video:** subida de archivo y grabación desde el celular.
4. **Carga real:** importador de archivo + sincronización; ROI de OCR en la UI; dejar de usar `0.0`.
5. **Geometría arbitraria:** nodos válidos, máscara y deformación sin grilla.
6. **Resultados:** gráficas, mapas sobre la imagen, módulo de elasticidad y extensómetro virtual para tracción y compresión.
7. **Exportación:** CSV → JPG → PDF, con metadatos de reproducibilidad.
8. **Validación y documentación** para la conferencia (sintéticos + extensómetro).
9. **Ensayos adicionales:** flexión, cortante/conexiones y momento en pórticos.

El detalle tarea por tarea está en [todo.md](todo.md).
