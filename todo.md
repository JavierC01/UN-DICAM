# TODO — UN-DICAM

Estado al 2026-10-19. Contexto y prioridades en [plan.md](plan.md).

Leyenda: `[x]` completada · `[~]` parcialmente completada · `[ ]` pendiente

---

## ✅ Completadas

### Infraestructura
- [x] `docker-compose` con backend, worker Celery, Redis y PostgreSQL
- [x] Dockerfile con OpenCV y `tesseract-ocr`
- [x] Configuración por `.env`, CORS y montaje de `/storage`
- [x] Endpoints `/` y `/health`
- [x] Creación de tablas al arrancar y espera a la base de datos
- [x] Suite de tests backend (23 pasan, 1 se omite sin Tesseract local)

### Cuentas y proyectos
- [x] Modelo `User` con hash PBKDF2
- [x] `POST /auth/register` (409 si el correo existe) y `POST /auth/login` (401 si falla)
- [x] Pantallas Login y Registro conectadas a la API
- [x] CRUD de proyectos (`GET/POST /projects`, `GET/DELETE /projects/{id}`)
- [x] Pantalla de Proyectos: listar, crear, eliminar, estados, recarga al enfocar

### Configuración del ensayo
- [x] `POST /specimen/configure` y `GET /specimen/{project_id}` con persistencia
- [x] Pantalla Setup (calibración) con validación y resumen px/mm, mm/px, área
- [x] `GET /devices/cameras`, `POST /devices/open`, `GET /devices/frame/{source_id}`
- [x] Pantalla de Captura: cámara o archivo, vista previa del primer frame
- [x] `POST /tracking/validate` y `POST /tracking/mesh` (9 nodos en grilla 3×3) con persistencia
- [x] Pantalla Malla: marcar polígono, deshacer/limpiar, validación en vivo, construir malla, parámetros

### Motor DIC y análisis
- [x] Correlación ZNCC con Numba y búsqueda del pico
- [x] Refinamiento subpíxel por mínimos cuadrados
- [x] Rastreo de malla y cálculo de εxx, εyy, εxy por cuadrante
- [x] Tarea Celery `process_full_analysis` con progreso por frame
- [x] Generación de mapas JPG de deformación
- [x] `POST /analysis/start`, `GET /analysis/status/{id}`, `GET /analysis/results/{id}`, `DELETE /analysis/{id}`
- [x] Pantalla de Resultados: sondeo de estado, barra de progreso, cancelar, resumen de métricas
- [x] Cliente HTTP común en el frontend (`apiRequest`, `ApiError`, `NotFoundError`)

---

## 🟡 Parcialmente completadas

- [~] **Lectura de carga por OCR** — implementada en [ocr.py](backend/app/dic/ocr.py), integrada en la tarea y con tests, pero:
  - [ ] Commitear los cambios (`ocr.py`, `RoiCarga`, `specimen.py`, `tasks.py`, `test_ocr.py`)
  - [ ] Ejecutar el test real de Tesseract (instalar Tesseract en Windows o correr tests en Docker)
  - [ ] No usar `0.0` cuando el OCR falla en un frame: descartar o interpolar el punto y contar fallos
- [~] **ROI de carga** — el backend la acepta y la usa, pero Setup siempre envía `roi_carga: null`
  - [ ] UI para dibujar el rectángulo de la carga sobre el primer frame
  - [ ] Enviar la ROI en `/specimen/configure` (o un endpoint aparte, porque Setup ocurre antes de tener frame)
- [~] **Autenticación** — registro y login funcionan, pero no hay sesión
  - [ ] Emitir JWT en el login y validarlo en los endpoints
  - [ ] Guardar el token en el frontend y enviarlo en `apiRequest`
  - [ ] Cerrar sesión
- [~] **Calibración** — funciona, pero `long_calibracion_px` se escribe a mano
  - [ ] Medirlo con dos toques sobre el frame
- [~] **Fuente de video**
  - [ ] Endpoint de subida de video (`python-multipart` ya instalado) y UI para elegir archivo
  - [ ] Resolver cámaras en Docker: `CAP_DSHOW` solo funciona en Windows nativo; evaluar `expo-camera` (instalado, sin usar)
- [~] **Pantalla de Resultados** — muestra estado y métricas, pero no curvas ni mapas
  - [ ] Gráfica carga–desplazamiento
  - [ ] Gráfica esfuerzo–deformación
  - [ ] Mostrar mapas εxx, εyy, εxy (anteponer el host a las URLs `/storage/...`)
  - [ ] Quitar el bloque obsoleto de "resultados pendientes" (manejo de 501)
- [~] **Parámetros de análisis** — `step_size` se envía pero el backend lo ignora
- [~] **Estados de análisis y proyecto**
  - [ ] Marcar `Analysis` como `running` al empezar
  - [ ] Actualizar el `Project` cuando el análisis falla o se cancela (hoy se queda en `in_progress`)
  - [ ] Agregar etiquetas `failed`/`revoked` en la pantalla de Proyectos
- [~] **WebSocket de progreso** — `/analysis/ws/{task_id}` solo responde "connected"; implementar o eliminar
- [~] **Manual de usuario** — la pantalla existe con texto de ejemplo; escribir el contenido real
- [~] **Pantalla de Reportes** — existe pero el botón no hace nada

---

## 🔴 Pendientes

### Resultados y exportación
- [ ] Implementar `export_results` en [export.py](backend/app/dic/export.py)
- [ ] `GET /export/csv/{analysis_id}` (curvas y métricas; `pandas` ya instalado)
- [ ] `GET /export/jpg/{analysis_id}` (mapas y gráficas)
- [ ] `GET /export/pdf/{analysis_id}` (reporte técnico; `reportlab` ya instalado)
- [ ] `GET /projects/{id}/analyses` para listar el historial de análisis
- [ ] Conectar la pantalla de Reportes: elegir análisis y descargar/compartir CSV, PDF, JPG
- [ ] Verificar ejes de `curva_desplaz_carga` (hoy `x = carga`, `y = desplazamiento`)

### Datos y backend
- [ ] Agregar `owner_id` a `Project` y filtrar proyectos por usuario
- [ ] `GET /tracking/{project_id}` para recuperar la malla guardada
- [ ] Migraciones con Alembic
- [ ] Rastreo incremental (actualizar la imagen de referencia) para deformaciones grandes
- [ ] Eliminar duplicados entre `app/dic/` y `app/services/` (dispositivos/devices, rastreo/tracking, analisis/analysis)
- [ ] Eliminar o usar el modelo `ImagePair`

### Seguridad
- [ ] Proteger todos los endpoints con autenticación
- [ ] Restringir `CORS_ORIGINS`
- [ ] Validar rutas de archivo en `source_id` (hoy se puede abrir cualquier ruta del servidor)
- [ ] Validaciones de formulario en el frontend (correo, longitud de contraseña)

### Calidad y documentación
- [ ] Tests de rutas: auth, proyectos, export
- [ ] Tests del frontend
- [ ] Validar el DIC con un video de referencia de desplazamiento conocido
- [ ] Quitar del repo `backend/__pycache__/`, `.expo/`, `frontend/.expo/` y `backend/package.json`
- [ ] README: flujo completo, `EXPO_PUBLIC_API_URL`, cómo correr el worker sin Docker
