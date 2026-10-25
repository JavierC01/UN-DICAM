# Plan de trabajo — UN-DICAM

Estado al 2026-10-25. Basado en el código de `main` (último commit revisado: `8ea32b4`).

UN-DICAM es una herramienta **open source** de Correlación Digital de Imágenes (DIC) 2D con una sola cámara, para caracterizar materiales y elementos de construcción: probetas de madera y concreto, conexiones metálicas no rectangulares, vigas CLT y CLBT, y núcleos de vigas y columnas. Soporta ensayos de tracción, compresión, flexión, cortante/conexiones y momento en pórticos, y tiene un objetivo académico: presentar el DIC como metodología alterna a los ensayos convencionales en la Digital Twins Engineering Conference 2027.

El usuario calibra el objeto, sube o graba un video (o usa una cámara en vivo), marca la región de interés, y el backend rastrea una malla de nodos frame a frame para obtener desplazamientos, deformaciones, carga (importada de la máquina o leída por OCR), esfuerzo y propiedades del material.

**Arquitectura:** FastAPI + SQLAlchemy (PostgreSQL) + Celery/Redis en el backend; Expo / React Native en el frontend, organizado con **diseño atómico**; todo orquestado con `docker-compose`.

## Resumen del estado

| Fase | Tema | Estado |
|---|---|---|
| 1 | Infraestructura base | ✅ Completada |
| 2 | Cuentas de usuario y proyectos | 🟡 Parcial |
| 3 | Configuración del ensayo (probeta, video, malla) | 🟡 Parcial |
| 4 | Motor DIC y análisis asíncrono | 🟡 Casi completa (para grilla rectangular) |
| 5 | Resultados, exportación y reportes | 🔴 Pendiente (mayormente) |
| 6 | Calidad, seguridad, open source y validación | 🔴 Pendiente |
| 7 | Geometría arbitraria, tipos de ensayo y carga | 🔴 Pendiente |
| 8 | Diseño atómico del frontend | 🔴 Pendiente |

El flujo principal ya funciona de punta a punta: **login → proyecto → calibración → fuente de video → malla → análisis → estado/resumen**. Desde el 21-oct la malla admite `filas × columnas` configurables (2–20). Lo que falta es, sobre todo: (a) que la carga se lea de verdad (hoy es 0, así que el esfuerzo también); (b) que la malla y la deformación funcionen en formas no rectangulares; (c) mostrar y exportar los resultados; (d) proteger la API y preparar el proyecto para publicarse con validación científica.

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
- Modelo `User`, registro (`/auth/register`) y login (`/auth/login`) con contraseñas PBKDF2.
- Pantallas de Login y Registro conectadas a la API, con manejo de errores (401, 409, sin conexión).
- CRUD de proyectos (listar, crear, ver, eliminar) y pantalla de Proyectos con estados.

**Falta**
- **Sesión/token:** el login solo devuelve el usuario; no se emite JWT ni se guarda sesión en el frontend. Cualquier endpoint es accesible sin autenticar.
- **Proyectos por usuario:** `Project` no tiene `owner_id`; todos los usuarios ven todos los proyectos.
- Cerrar sesión; validaciones de formulario (correo, longitud de contraseña) en el frontend.

## Fase 3 — Configuración del ensayo 🟡

**Hecho**
- Calibración de probeta: cálculo de px/mm, mm/px y área; persistencia en `specimen_config`; pantalla Setup que carga la configuración existente.
- Fuentes de video: listar cámaras, abrir cámara o archivo, obtener el primer frame en base64; pantalla de Captura.
- Malla de rastreo: validación del polígono, distribución de nodos en grilla `filas × columnas` (por defecto 3×3, configurable de 2 a 20), persistencia en `tracking_meshes`; pantalla Malla con toques sobre la imagen, deshacer/limpiar y parámetros.
- Esquema `RoiCarga` tipado para la región donde aparece la carga en el video.

**Falta**
- **Subida de video:** hoy el archivo se indica como ruta del servidor; falta un endpoint de upload (`python-multipart` ya está instalado), su UI y la validación de rutas.
- **Grabación desde el celular:** usar `expo-camera` (instalado, sin usar), grabar y subir el video.
- **Cámara en vivo en el PC:** `CAP_DSHOW` solo existe en Windows; en Linux/Docker no hay acceso a cámaras USB. Definir la estrategia (backend nativo en Windows, `CAP_V4L2` en Linux, o grabar desde el móvil).
- **ROI de la carga:** Setup envía siempre `roi_carga: null`, por lo que el OCR nunca se ejecuta. Se resuelve con el organismo `FrameAnnotator` (Fase 8), modo `rect`.
- **Medir `long_calibracion_px` sobre la imagen** con dos toques (`FrameAnnotator`, modo `line`) en lugar de escribirlo a mano.
- Recuperar la malla guardada al volver a la pantalla (no existe `GET /tracking/{project_id}`).

## Fase 4 — Motor DIC y análisis asíncrono 🟡

**Hecho**
- Correlación ZNCC acelerada con Numba, búsqueda del pico entero y refinamiento subpíxel por mínimos cuadrados.
- Rastreo de la malla y cálculo de deformaciones εxx, εyy, εxy por celda `(filas-1) × (columnas-1)`.
- Tarea Celery `process_full_analysis`: lee el video, procesa frame a frame, reporta progreso, genera mapas JPG y guarda resultados en `results`.
- Endpoints de inicio, estado, resultados y cancelación; pantalla de Resultados con sondeo cada 1.5 s, barra de progreso y cancelación.
- Lectura de carga por OCR (recorte de ROI, binarización Otsu, Tesseract, parseo numérico) integrada en la tarea, con tests. *Verificar con `git status` que `ocr.py`, `RoiCarga` y `test_ocr.py` estén commiteados.*

**Falta**
- Cuando el OCR falla en un frame hoy se usa `0.0`, lo que mete puntos falsos en las curvas. Descartar o interpolar el punto y contar los fallos (principio de rigor científico).
- `step_size` se recibe pero el backend lo ignora.
- La referencia es siempre el frame inicial; para deformaciones grandes conviene actualizar la referencia (rastreo incremental).
- Revisar los ejes de `curva_desplaz_carga` (hoy `x = carga`, `y = desplazamiento`; lo usual es al revés).
- Estados coherentes: `Analysis` nunca pasa a `running`; si el análisis falla o se cancela, el `Project` se queda en `in_progress`.
- El WebSocket `/analysis/ws/{task_id}` es un stub: implementarlo o eliminarlo.
- Código duplicado entre `app/dic/` y `app/services/` (`dispositivos.py` vs `devices.py`, `rastreo.py` vs `tracking.py`, `analisis.py` vs `services/analysis.py`); el modelo `ImagePair` no se usa.

## Fase 5 — Resultados, exportación y reportes 🔴

**Hecho**
- El backend guarda curvas, rutas de los mapas y métricas resumen, y `GET /analysis/results/{id}` las devuelve.
- La pantalla de Resultados muestra esfuerzo máximo, deformación máxima y coeficiente de correlación medio.

**Falta**
- **Gráficas** carga–desplazamiento y esfuerzo–deformación (`CurveChart`).
- **Mapas** εxx, εyy, εxy: anteponer el host del API a las URLs `/storage/...` y, a futuro, dibujarlos sobre el primer frame.
- **Exportación** CSV, PDF y JPG: los endpoints `/export/*` devuelven 501 y `app/dic/export.py` lanza `NotImplementedError`. `pandas` y `reportlab` ya están instalados. Los reportes deben incluir los metadatos de reproducibilidad (parámetros, versión, hash del video, método de carga).
- **Historial:** no hay endpoint para listar los análisis de un proyecto.
- **Pantalla de Reportes:** estática (botón sin acción).
- Quitar el mensaje obsoleto de "resultados aún no disponibles" (código 501) en Resultados.

## Fase 6 — Calidad, seguridad, open source y validación 🔴

- Autenticación obligatoria en todos los endpoints (depende de la Fase 2) y CORS restringido por defecto.
- Validar `source_id` de tipo archivo para evitar leer rutas arbitrarias del servidor; límite de tamaño en la subida.
- Tests de integración de rutas (auth, proyectos, export) y tests de frontend (hoy no hay ninguno).
- Manual de usuario real (hoy es texto de ejemplo).
- **Open source:** archivo `LICENSE` **[DECIDIR]**, README bilingüe, `CONTRIBUTING.md`, integración continua con pytest, sin credenciales ni videos en el repo, atribución a código de terceros.
- **Validación científica:** carpeta `validation/` con imágenes sintéticas de desplazamiento conocido y comparación contra extensómetro/LVDT/galga en ensayos reales; documentar la resolución de deformación y la limitación 2D.

## Fase 7 — Geometría arbitraria, tipos de ensayo y carga 🔴

**Geometría arbitraria** (hoy el polígono solo define una máscara; los nodos son una grilla sobre el rectángulo envolvente y la deformación asume celdas rectangulares)
- Nodos válidos solo donde el subset completo cae dentro de la forma (máscara erosionada por la mitad del subset); marcar los inválidos.
- Deformación sin depender de la grilla: celdas con 4 esquinas válidas (versión mínima) y luego triangulación con elementos de deformación constante o ventana local.
- Mapas con máscara y dibujados sobre el primer frame.
- Nodo "central" como el nodo válido más cercano al centroide del polígono.
- Unificar la distribución de nodos en un solo lugar (hoy está duplicada).
- Segmentación automática de la forma (opcional) para no marcar vértices a mano.

**Tipos de ensayo** (`dic/ensayos/`, estrategia por tipo)
- Interfaz común: cálculo de esfuerzo, extensómetro virtual y módulo.
- Tracción y compresión (extensómetro entre dos puntos, módulo de elasticidad con rango elegido por el usuario).
- Flexión (deflexión; CLT/CLBT).
- Cortante y conexiones metálicas (deslizamiento relativo).
- Momento en pórticos (rotación).
- Definir las normas aplicables por material **[DECIDIR]**.

**Carga**
- Importador de archivo de la máquina (CSV/XLSX) con mapeo de columnas y unidades.
- Sincronización temporal carga↔frames (offset, evento de inicio, interpolación).
- OCR como alternativa para máquinas sin exportación, con ROI dibujada en la UI y conteo de fallos.

## Fase 8 — Diseño atómico del frontend 🔴

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
