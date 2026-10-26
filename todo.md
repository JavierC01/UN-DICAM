# TODO — UN-DICAM

Estado al 2026-10-26. Contexto y prioridades en [plan.md](plan.md); reglas para agentes en [CLAUDE.md](CLAUDE.md).

Leyenda: `[x]` completada · `[~]` parcialmente completada · `[ ]` pendiente · **[DECIDIR]** requiere decisión del autor

---

## ✅ Completadas

### Infraestructura
- [x] `docker-compose` con backend, worker Celery, Redis y PostgreSQL
- [x] Dockerfile con OpenCV y `tesseract-ocr`
- [x] Configuración por `.env`, CORS y montaje de `/storage`
- [x] Endpoints `/` y `/health`
- [x] Creación de tablas al arrancar y espera a la base de datos
- [x] Suite de tests backend (68 pasan, 1 se omite sin Tesseract local)
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

### Completadas el 2026-10-26 (tareas parciales y Fase 7)

**Antes parciales**
- [x] OCR: un fallo de lectura ya no vale `0.0`; el punto queda nulo, se cuenta (`carga.fallos_ocr`) y se advierte
- [x] ROI de carga dibujada sobre el frame (`FrameAnnotator`, modo `rect`) y enviada en `/specimen/configure` (Captura ahora va antes que Configuración)
- [x] JWT (HS256 con la biblioteca estándar) emitido en `/auth/login` y exigido en todos los endpoints salvo `/auth`; token guardado con `expo-secure-store` (localStorage en web), enviado por `apiRequest`, cierre de sesión y regreso al login ante un 401
- [x] `long_calibracion_px` medido con dos toques (`FrameAnnotator`, modo `line`)
- [x] `POST /devices/upload` (extensión validada, límite `MAX_UPLOAD_MB`, verificación de que el archivo es un video legible) y UI con `expo-document-picker`
- [x] Cámaras: `CAP_DSHOW` en Windows, `CAP_V4L2` en Linux, `CAP_ANY` en otros
- [x] Grabación desde el celular con `expo-camera` y subida del video
- [x] Resultados: gráficas propias con `react-native-svg` (`CurveChart`), mapas con el host antepuesto, advertencias, información de carga; quitado el bloque de 501
- [x] `step_size` eliminado del request (no tenía efecto): el paso de nodos lo fija la malla `filas × columnas` y se guarda como `paso_nodos_px` en los metadatos
- [x] Estados: `Analysis` pasa a `running`; si falla, `Project` queda `failed`; si se cancela, `revoked`; etiquetas en Proyectos
- [x] WebSocket `/analysis/ws/{task_id}` eliminado (era un stub; la app usa sondeo)
- [x] Manual de usuario con el flujo real
- [x] Pantalla de Reportes: historial por proyecto y descarga CSV/PDF/JPG

**Fase 7 y relacionadas**
- [x] Nodos válidos solo donde el subset completo cae dentro de la forma (máscara erosionada); inválidos marcados en `MeshResponse.validos` y `TrackingMesh.validos`, sin forzarlos al borde
- [x] `calcular_deformaciones` (grilla): celda `NaN` si alguna esquina es inválida; medias sin los `NaN`
- [x] Deformación por triangulación de Delaunay con elementos CST (`deformacion_triangulos`), sin triángulos que crucen huecos
- [x] Nodo central = nodo válido más cercano al centroide del polígono
- [x] Mapas dibujados sobre el primer frame (`tripcolor`, triángulos sin dato transparentes)
- [x] Distribución de nodos unificada en `dic/rastreo.py`; borrados `dic/dispositivos.py`, `dic/analisis.py`, `services/analysis.py` y el modelo `ImagePair`
- [x] Tests con hueso de perro, entalla y forma en L (geometría, triangulación, CST y estiramiento sintético rastreado)
- [x] Interfaz `Ensayo` en `dic/ensayos/` con tracción, compresión (extensómetro entre dos puntos), flexión (deflexión relativa a los apoyos), cortante (deslizamiento relativo) y pórtico (rotación y momento con brazo)
- [x] Propiedad por ajuste lineal en el rango que elige el usuario (`POST /analysis/{id}/propiedad`, rango en x o fracción de la respuesta máxima), con rango, pendiente y R²
- [x] Selector de tipo de ensayo y parámetros en Configuración; puntos del extensómetro sobre la malla (`PUT /tracking/{id}/puntos-ensayo`, validados dentro de la triangulación)
- [x] Importador CSV/XLSX (`openpyxl`) con mapeo de columnas y unidades (N, kN, kgf, tf, lbf; s, ms, min)
- [x] Sincronización carga↔frames: offset, evento de inicio por umbral de carga e interpolación a los tiempos de frame
- [x] Fuente de carga por proyecto: archivo, OCR o ninguna; el resultado reporta interpolados, descartados y fallos
- [x] `export_results` reemplazado por `exportar_csv/jpg/pdf`; endpoints `/export/csv|jpg|pdf/{id}` con metadatos de reproducibilidad
- [x] `GET /projects/{id}/analyses` (historial)
- [x] Ejes de `curva_desplaz_carga` corregidos: `x` = desplazamiento, `y` = carga
- [x] `source_id` de archivo restringido a nombres dentro de `storage/uploads/`

---

## 🟡 Parcialmente completadas

- [~] **Lectura de carga por OCR**
  - [ ] Ejecutar el test real de Tesseract en Docker (`docker compose run --rm backend pytest tests/test_ocr.py`); en el entorno de desarrollo no estaban ni Tesseract ni el daemon de Docker
- [~] **Frontend sin verificar en dispositivo:** la sintaxis y los imports se revisaron, pero `pnpm install` lo bloqueó la política de cadena de suministro de pnpm (`semver@6.3.1`, *trust downgrade*); falta instalar las dependencias nuevas (`react-native-svg`, `expo-document-picker`, `expo-secure-store`) y probar el flujo en Android/iOS/web

---

## 🔴 Pendientes

### Fase 7 (opcional)
- [ ] Segmentación automática de la forma (`grabCut`/Otsu) para no marcar vértices a mano
- [ ] Definir las normas aplicables por material **[DECIDIR]** (hoy el usuario escribe el rango del ajuste)
- [ ] Módulo de elasticidad a flexión (E global con luz e inercia), además de la rigidez

### Resultados y exportación
- [ ] Mapas de deformación de cualquier frame (hoy solo el último)
- [ ] Compartir el archivo desde la app en lugar de abrirlo en el navegador

### Datos y backend
- [ ] Agregar `owner_id` a `Project` y filtrar proyectos por usuario
- [ ] `GET /tracking/{project_id}` para recuperar la malla guardada
- [ ] Migraciones con Alembic (mientras tanto, los `ALTER` están en el README)
- [ ] Rastreo incremental (actualizar la imagen de referencia) para deformaciones grandes

### Seguridad
- [ ] Restringir `CORS_ORIGINS`
- [ ] Descargas con enlaces firmados de un solo uso en lugar de `?token=`; `/storage` hoy es público
- [ ] El límite de subida se aplica al escribir el archivo, después de que el servidor recibió el cuerpo: limitarlo también en el proxy
- [ ] Validaciones de formulario en el frontend (correo, longitud de contraseña)

### Diseño atómico del frontend (Fase 8)
- [~] **Tokens:** `styles/theme.js` ya tiene `colors`, `spacing`, `typography`, `radii` y `touchTarget`; las pantallas reescritas los usan, faltan Login, Registro y Proyectos
- [ ] **Átomos:** Button, TextField, Typography, Label, Icon, Badge, Spinner, Divider (cada uno en `components/atoms/<Nombre>/`)
- [ ] **Moléculas:** FormField, SegmentedControl, MetricCard, ProgressBar, InlineMessage, KeyValueRow, ImageWithCaption
- [x] **Organismo `FrameAnnotator`** con modos `line` (calibración), `rect` (ROI de carga), `polygon` (malla) y `points` (extensómetro); coordenadas en píxeles del frame original
- [x] **`CurveChart`** propio con `react-native-svg` y molécula **`SegmentedControl`**
- [ ] **Otros organismos:** LoginForm, RegisterForm, ProjectList, SpecimenForm, VideoSourcePicker, MeshParametersPanel, AnalysisProgressPanel, ResultsSummary, StrainMapGallery, ExportPanel
- [ ] **Templates:** AuthTemplate, ScreenTemplate, WizardTemplate (indicador de pasos Setup → Captura → Malla → Resultados)
- [ ] **Migrar pantallas, una por PR:** Login → Registro → Proyectos → Setup → Captura → Malla → Resultados → Reportes → Manual
- [ ] Hooks de datos (`useAnalysisStatus`, `useFirstFrame`) para que las pantallas queden como páginas delgadas
- [ ] Verificar la regla de imports `atoms ← molecules ← organisms ← templates ← screens` (ningún componente de UI llama a `api/` ni a `navigation`)
- [ ] Accesibilidad: `accessibilityLabel`, áreas táctiles de al menos 44 pt
- [ ] Textos de usuario centralizados en `src/i18n/es.js` **[DECIDIR: ¿traducir la app?]**

### Calidad, open source y validación
- [~] Tests de rutas: auth, export, cargas, malla y análisis cubiertos; faltan CRUD de proyectos
- [ ] Tests del frontend (jest-expo + Testing Library, instalados con pnpm), empezando por átomos y moléculas
- [ ] Carpeta `validation/` con imágenes sintéticas de desplazamiento conocido (traslación rígida, estiramiento uniforme, gradiente) y reporte de error medio y desviación
- [ ] Validar contra extensómetro/LVDT/galga en ensayos reales
- [ ] Documentar la limitación 2D (movimiento fuera de plano) y la resolución de deformación alcanzada
- [ ] Archivo `LICENSE` **[DECIDIR: MIT/Apache-2.0 o GPL]**
- [ ] README completo y bilingüe, `CONTRIBUTING.md`
- [ ] Integración continua con pytest
- [ ] Atribución de código de terceros (revisar licencias de dependencias y de cualquier código reutilizado)
- [ ] Quitar del repo `backend/__pycache__/`, `.expo/`, `frontend/.expo/` y `backend/package.json`
- [x] README: flujo completo, `SECRET_KEY`, `ALTER` de esquema, cómo correr el worker sin Docker
