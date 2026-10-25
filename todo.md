# TODO — UN-DICAM

Estado al 2026-10-25. Contexto y prioridades en [plan.md](plan.md); reglas para agentes en [CLAUDE.md](CLAUDE.md).

Leyenda: `[x]` completada · `[~]` parcialmente completada · `[ ]` pendiente · **[DECIDIR]** requiere decisión del autor

---

## ✅ Completadas

### Infraestructura
- [x] `docker-compose` con backend, worker Celery, Redis y PostgreSQL
- [x] Dockerfile con OpenCV y `tesseract-ocr`
- [x] Configuración por `.env`, CORS y montaje de `/storage`
- [x] Endpoints `/` y `/health`
- [x] Creación de tablas al arrancar y espera a la base de datos
- [x] Suite de tests backend (23 pasan, 1 se omite sin Tesseract local)
- [x] `CLAUDE.md` con guía para agentes de codificación

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
- [x] `POST /tracking/validate` y `POST /tracking/mesh` con persistencia
- [x] Malla configurable `filas × columnas` (2–20, por defecto 3×3) en backend y pantalla Malla
- [x] Pantalla Malla: marcar polígono, deshacer/limpiar, validación en vivo, construir malla, parámetros

### Motor DIC y análisis
- [x] Correlación ZNCC con Numba y búsqueda del pico
- [x] Refinamiento subpíxel por mínimos cuadrados
- [x] Rastreo de malla y cálculo de εxx, εyy, εxy por celda `(filas-1) × (columnas-1)`
- [x] Tarea Celery `process_full_analysis` con progreso por frame
- [x] Generación de mapas JPG de deformación
- [x] `POST /analysis/start`, `GET /analysis/status/{id}`, `GET /analysis/results/{id}`, `DELETE /analysis/{id}`
- [x] Pantalla de Resultados: sondeo de estado, barra de progreso, cancelar, resumen de métricas
- [x] Cliente HTTP común en el frontend (`apiRequest`, `ApiError`, `NotFoundError`)

---

## 🟡 Parcialmente completadas

- [~] **Lectura de carga por OCR** — implementada en [ocr.py](backend/app/dic/ocr.py), integrada en la tarea y con tests, pero:
  - [ ] Verificar con `git status` que `ocr.py`, `RoiCarga`, `specimen.py`, `tasks.py` y `test_ocr.py` estén commiteados
  - [ ] Ejecutar el test real de Tesseract (instalar Tesseract en Windows o correr tests en Docker)
  - [ ] No usar `0.0` cuando el OCR falla en un frame: descartar o interpolar el punto y contar fallos
- [~] **ROI de carga** — el backend la acepta y la usa, pero Setup siempre envía `roi_carga: null`
  - [ ] Dibujar el rectángulo sobre el primer frame con `FrameAnnotator` (modo `rect`)
  - [ ] Enviar la ROI en `/specimen/configure` (o un endpoint aparte, porque Setup ocurre antes de tener frame)
- [~] **Autenticación** — registro y login funcionan, pero no hay sesión
  - [ ] Emitir JWT en el login y validarlo en los endpoints
  - [ ] Guardar el token en el frontend y enviarlo en `apiRequest`
  - [ ] Cerrar sesión
- [~] **Calibración** — funciona, pero `long_calibracion_px` se escribe a mano
  - [ ] Medirlo con dos toques sobre el frame (`FrameAnnotator`, modo `line`)
- [~] **Fuente de video**
  - [ ] Endpoint de subida de video (`python-multipart` ya instalado) y UI para elegir archivo
  - [ ] Resolver cámaras: `CAP_DSHOW` solo funciona en Windows nativo; en Linux usar `CAP_V4L2` o grabar desde el móvil
  - [ ] Grabación desde el celular con `expo-camera` (instalado, sin usar) y subida del video
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

### Geometría arbitraria (Fase 7)
- [ ] Nodos válidos solo donde el subset completo cae dentro de la forma (máscara erosionada por `subset_size // 2`); marcar los inválidos en el esquema y la base de datos
- [ ] `calcular_deformaciones`: calcular una celda solo si sus 4 esquinas son válidas (resto `NaN`); mapas con `masked_invalid`
- [ ] Deformación sin grilla: triangulación (Delaunay) con elementos de deformación constante, o ventana local
- [ ] Nodo central = nodo válido más cercano al centroide del polígono
- [ ] Mapas de deformación dibujados sobre el primer frame
- [ ] Unificar la distribución de nodos (hoy en `services/tracking.py` y `dic/rastreo.py`)
- [ ] Tests con formas no rectangulares (hueso de perro, entalla, forma en L)
- [ ] (Opcional) Segmentación automática de la forma (`grabCut`/Otsu) para no marcar vértices a mano

### Tipos de ensayo y propiedades (Fase 7)
- [ ] Interfaz `Ensayo` en `dic/ensayos/`: esfuerzo, extensómetro virtual y módulo por tipo
- [ ] Tracción y compresión: extensómetro entre dos puntos y módulo de elasticidad con rango elegido por el usuario (reportar rango y R²)
- [ ] Flexión (vigas, CLT/CLBT): deflexión
- [ ] Cortante y conexiones metálicas: deslizamiento relativo
- [ ] Momento en pórticos: rotación
- [ ] Definir las normas aplicables por material **[DECIDIR]**
- [ ] Selector de tipo de ensayo en la configuración del proyecto

### Carga desde la máquina (Fase 7)
- [ ] Importador CSV/XLSX con mapeo de columnas y unidades
- [ ] Sincronización temporal carga↔frames (offset, evento de inicio, interpolación a tiempos de frame)
- [ ] Elegir la fuente de carga por proyecto: archivo de la máquina u OCR
- [ ] Reportar en el resultado cuántos puntos se interpolaron o se descartaron

### Resultados y exportación
- [ ] Implementar `export_results` en [export.py](backend/app/dic/export.py)
- [ ] `GET /export/csv/{analysis_id}` (curvas y métricas; `pandas` ya instalado)
- [ ] `GET /export/jpg/{analysis_id}` (mapas y gráficas)
- [ ] `GET /export/pdf/{analysis_id}` (reporte técnico; `reportlab` ya instalado)
- [ ] Incluir metadatos de reproducibilidad en cada exportación (parámetros, calibración, método de carga, hash del video, versión/commit)
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
- [ ] Validar rutas de archivo en `source_id` (hoy se puede abrir cualquier ruta del servidor); los videos subidos viven en `storage/uploads/`
- [ ] Límite de tamaño y validación de extensión en la subida de video
- [ ] Validaciones de formulario en el frontend (correo, longitud de contraseña)

### Diseño atómico del frontend (Fase 8)
- [ ] **Tokens:** ampliar `styles/theme.js` con `colors`, `spacing`, `typography`, `radii`; eliminar colores y tamaños literales
- [ ] **Átomos:** Button, TextField, Typography, Label, Icon, Badge, Spinner, Divider (cada uno en `components/atoms/<Nombre>/`)
- [ ] **Moléculas:** FormField, SegmentedControl, MetricCard, ProgressBar, InlineMessage, KeyValueRow, ImageWithCaption
- [ ] **Organismo `FrameAnnotator`** con modos `line` (calibración), `rect` (ROI de carga) y `polygon` (malla); coordenadas devueltas en píxeles del frame original
- [ ] **Otros organismos:** LoginForm, RegisterForm, ProjectList, SpecimenForm, VideoSourcePicker, MeshParametersPanel, AnalysisProgressPanel, ResultsSummary, CurveChart (evaluar `react-native-svg` antes de añadir una librería de gráficas), StrainMapGallery, ExportPanel
- [ ] **Templates:** AuthTemplate, ScreenTemplate, WizardTemplate (indicador de pasos Setup → Captura → Malla → Resultados)
- [ ] **Migrar pantallas, una por PR:** Login → Registro → Proyectos → Setup → Captura → Malla → Resultados → Reportes → Manual
- [ ] Hooks de datos (`useAnalysisStatus`, `useFirstFrame`) para que las pantallas queden como páginas delgadas
- [ ] Verificar la regla de imports `atoms ← molecules ← organisms ← templates ← screens` (ningún componente de UI llama a `api/` ni a `navigation`)
- [ ] Accesibilidad: `accessibilityLabel`, áreas táctiles de al menos 44 pt
- [ ] Textos de usuario centralizados en `src/i18n/es.js` **[DECIDIR: ¿traducir la app?]**

### Calidad, open source y validación
- [ ] Tests de rutas: auth, proyectos, export
- [ ] Tests del frontend (jest-expo + Testing Library, instalados con pnpm), empezando por átomos y moléculas
- [ ] Carpeta `validation/` con imágenes sintéticas de desplazamiento conocido (traslación rígida, estiramiento uniforme, gradiente) y reporte de error medio y desviación
- [ ] Validar contra extensómetro/LVDT/galga en ensayos reales
- [ ] Documentar la limitación 2D (movimiento fuera de plano) y la resolución de deformación alcanzada
- [ ] Archivo `LICENSE` **[DECIDIR: MIT/Apache-2.0 o GPL]**
- [ ] README completo y bilingüe, `CONTRIBUTING.md`
- [ ] Integración continua con pytest
- [ ] Atribución de código de terceros (revisar licencias de dependencias y de cualquier código reutilizado)
- [ ] Quitar del repo `backend/__pycache__/`, `.expo/`, `frontend/.expo/` y `backend/package.json`
- [ ] README: flujo completo, `EXPO_PUBLIC_API_URL`, cómo correr el worker sin Docker
