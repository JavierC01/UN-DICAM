# Plan de trabajo — UN-DICAM

Estado al 2026-10-19. Basado en la revisión del código en `main` (commit `c02c2b41`) más los cambios sin commitear de OCR.

UN-DICAM es una herramienta de Correlación Digital de Imágenes (DIC) para ensayos de tracción: el usuario calibra la probeta, abre un video o cámara, dibuja la región de interés, y el backend rastrea una malla de 9 nodos frame a frame para obtener desplazamientos, deformaciones, carga (vía OCR) y esfuerzo.

**Arquitectura:** FastAPI + SQLAlchemy (PostgreSQL) + Celery/Redis en el backend; Expo / React Native en el frontend; todo orquestado con `docker-compose`.

## Resumen del estado

| Fase | Tema | Estado |
|---|---|---|
| 1 | Infraestructura base | ✅ Completada |
| 2 | Cuentas de usuario y proyectos | 🟡 Parcial |
| 3 | Configuración del ensayo (probeta, video, malla) | 🟡 Parcial |
| 4 | Motor DIC y análisis asíncrono | 🟡 Casi completa |
| 5 | Resultados, exportación y reportes | 🔴 Pendiente (mayormente) |
| 6 | Calidad, seguridad y despliegue | 🔴 Pendiente |

El flujo principal ya funciona de punta a punta: **login → proyecto → calibración → fuente de video → malla → análisis → estado/resumen**. Lo que falta es, sobre todo, (a) que la carga se lea de verdad (hoy es siempre 0, así que el esfuerzo también), (b) mostrar y exportar los resultados, y (c) proteger la API.

---

## Fase 1 — Infraestructura base ✅

- `docker-compose.yml` con backend, worker de Celery, Redis y PostgreSQL.
- `Dockerfile` con OpenCV y `tesseract-ocr` instalados.
- Configuración por `.env` ([backend/app/Core/config.py](backend/app/Core/config.py)), CORS, montaje de `/storage` como archivos estáticos.
- Endpoints `/` y `/health`, router versionado `/api/v1`.
- Creación de tablas al arrancar (`init_db` con `create_all`) y espera a la base de datos (`wait_for_db`).
- Suite de tests con pytest (23 pasan, 1 se omite si no hay Tesseract local).

**Pendiente menor:** migraciones con Alembic (hoy cualquier cambio de modelo exige borrar la base), y limpiar archivos versionados que no deberían estarlo (`__pycache__`, `.expo/`, `backend/package.json`).

## Fase 2 — Cuentas de usuario y proyectos 🟡

**Hecho**
- Modelo `User`, registro (`/auth/register`) y login (`/auth/login`) con contraseñas PBKDF2.
- Pantallas de Login y Registro conectadas a la API, con manejo de errores (401, 409, sin conexión).
- CRUD de proyectos (listar, crear, ver, eliminar) y pantalla de Proyectos con estados.

**Falta**
- **Sesión/token:** el login solo devuelve el usuario; no se emite JWT ni se guarda sesión en el frontend. Cualquier endpoint es accesible sin autenticar.
- **Proyectos por usuario:** `Project` no tiene `owner_id`; todos los usuarios ven todos los proyectos.
- Cerrar sesión, validaciones de formulario (formato de correo, longitud de contraseña) en el frontend.

## Fase 3 — Configuración del ensayo 🟡

**Hecho**
- Calibración de probeta: cálculo de px/mm, mm/px y área; persistencia en `specimen_config`; pantalla Setup que carga la configuración existente.
- Fuentes de video: listar cámaras, abrir cámara o archivo, obtener el primer frame en base64; pantalla de Captura.
- Malla de rastreo: validación del polígono, distribución de 9 nodos en grilla 3×3, persistencia en `tracking_meshes`; pantalla Malla con toques sobre la imagen, deshacer/limpiar y parámetros de análisis.
- Esquema `RoiCarga` tipado para la región donde aparece la carga en el video (sin commitear).

**Falta**
- **Selección de la ROI de carga en el frontend:** Setup envía siempre `roi_carga: null`, por lo que el OCR nunca se ejecuta en la práctica. Hay que permitir dibujar un rectángulo sobre el primer frame (probablemente en la pantalla de Captura o Malla, que es donde ya hay frame).
- **Medir `long_calibracion_px` sobre la imagen** en lugar de escribirlo a mano (dos toques sobre el frame).
- **Subida de video:** hoy el archivo se indica como ruta en el servidor; falta un endpoint de upload (ya está `python-multipart` en requirements) y su UI.
- **Cámaras en Docker:** se usa `cv2.CAP_DSHOW` (solo Windows); dentro del contenedor Linux no hay acceso a cámaras USB. Definir si la captura en vivo se hace con el backend nativo en Windows, o con `expo-camera` (ya instalado, sin usar) grabando desde el móvil y subiendo el video.
- Recuperar la malla guardada al volver a la pantalla (no existe `GET /tracking/{project_id}`).

## Fase 4 — Motor DIC y análisis asíncrono 🟡 (casi completa)

**Hecho**
- Correlación ZNCC acelerada con Numba, búsqueda del pico entero y refinamiento subpíxel por mínimos cuadrados.
- Rastreo de la malla de 9 nodos y cálculo de deformaciones εxx, εyy, εxy en los 4 cuadrantes.
- Tarea Celery `process_full_analysis`: lee el video, procesa frame a frame, reporta progreso, genera mapas JPG de deformación y guarda resultados en `results`.
- Endpoints de inicio, estado, resultados y cancelación; pantalla de Resultados con sondeo cada 1.5 s, barra de progreso y cancelación.
- Lectura de carga por OCR (recorte de ROI, binarización Otsu, Tesseract, parseo numérico) integrada en la tarea, con tests (sin commitear).

**Falta**
- Commitear el trabajo de OCR y verificar el test real con Tesseract instalado (en Docker sí lo está).
- Decidir qué hacer cuando el OCR falla en un frame: hoy se usa `0.0`, lo que mete puntos falsos en las curvas. Mejor descartar el punto o interpolar, y contar fallos.
- `step_size` se recibe pero el backend lo ignora.
- La referencia es siempre el frame inicial; para deformaciones grandes conviene actualizar la referencia (rastreo incremental).
- Revisar ejes de `curva_desplaz_carga`: hoy `x = carga`, `y = desplazamiento` (lo usual es al revés).
- Estados coherentes: el `Analysis` nunca pasa a `running`; si el análisis falla o se cancela, el `Project` se queda en `in_progress`.
- WebSocket `/analysis/ws/{task_id}` es un stub (se puede quitar o implementar; el sondeo ya funciona).
- Código duplicado entre `app/dic/` y `app/services/` (`dispositivos.py` vs `devices.py`, `rastreo.py` vs `tracking.py`, `analisis.py` vs `services/analysis.py`); el modelo `ImagePair` no se usa.

## Fase 5 — Resultados, exportación y reportes 🔴

**Hecho**
- El backend ya guarda curvas, rutas de los mapas y métricas resumen, y `GET /analysis/results/{id}` las devuelve.
- La pantalla de Resultados muestra esfuerzo máximo, deformación máxima y coeficiente de correlación medio.

**Falta**
- **Gráficas** de carga–desplazamiento y esfuerzo–deformación en Resultados (requiere una librería de gráficas para React Native).
- **Mostrar los mapas** εxx, εyy, εxy (las URLs son relativas `/storage/...`; hay que anteponer el host del API).
- **Exportación** CSV, PDF y JPG: los endpoints `/export/*` devuelven 501 y `app/dic/export.py` lanza `NotImplementedError`. `pandas` y `reportlab` ya están instalados para esto.
- **Historial:** no hay endpoint para listar los análisis de un proyecto, así que no se puede volver a ver un análisis pasado.
- **Pantalla de Reportes:** es estática (botón sin acción).
- Quitar el mensaje obsoleto de "resultados aún no disponibles" (código 501) en Resultados.

## Fase 6 — Calidad, seguridad y despliegue 🔴

- Autenticación obligatoria en todos los endpoints (depende de la Fase 2) y CORS restringido.
- Validar `source_id` de tipo archivo para evitar leer rutas arbitrarias del servidor.
- Tests del frontend (no hay ninguno) y tests de integración de rutas (auth, proyectos, export).
- Manual de usuario real (hoy es texto de ejemplo).
- README: documentar el flujo completo, variables `EXPO_PUBLIC_API_URL`, y cómo correr el worker sin Docker.
- Validación del método DIC con un video de referencia (comparar contra extensómetro o desplazamiento conocido).

---

## Orden recomendado

1. Commitear OCR y añadir la selección de ROI de carga en el frontend — sin esto el esfuerzo siempre es 0 y las curvas no sirven.
2. Mostrar gráficas y mapas en Resultados, y añadir el historial de análisis por proyecto.
3. Implementar exportación CSV → JPG → PDF y conectar la pantalla de Reportes.
4. Tokens de sesión, proyectos por usuario y protección de endpoints.
5. Subida de video / captura desde el móvil.
6. Limpieza (duplicados, estados, Alembic) y documentación.

El detalle tarea por tarea está en [todo.md](todo.md).
