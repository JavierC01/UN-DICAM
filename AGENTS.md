# UN-DICAM — Dirección del producto y reglas para agentes

> Borrador. Complementa (no reemplaza) los comandos y la descripción de arquitectura que ya están en `CLAUDE.md`.
> Los puntos marcados con **[DECIDIR]** son decisiones abiertas del autor: el agente debe preguntar antes de asumirlas.

## 1. Qué es y para quién

UN-DICAM es una herramienta **open source** de correlación digital de imágenes (DIC) 2D con una sola cámara, para caracterizar materiales y elementos de construcción como alternativa o complemento a los ensayos convencionales:

- Probetas de madera y concreto.
- Conexiones metálicas no rectangulares.
- Vigas CLT y CLBT.
- Núcleos de vigas y columnas.

Tiene dos usos: ensayos de laboratorio y sustento académico para la Digital Twins Engineering Conference 2027. Cualquier persona debe poder instalarla y usarla.

## 2. Alcance funcional

- **Tipos de ensayo:** tracción, compresión (concreto, núcleos), flexión (vigas, CLT/CLBT), cortante/conexiones metálicas y momento en pórticos.
- **Geometría:** arbitraria. Nunca asumir probeta rectangular ni una grilla completa de nodos.
- **Fuentes de video:** archivo subido, grabación desde el celular con la app, y cámara en vivo en el PC.
- **Carga:** (1) importar el archivo exportado por la máquina de ensayo (prioridad); (2) OCR del video para máquinas sin exportación.
- **Salidas:** mapas de deformación sobre la imagen, curvas carga–desplazamiento y esfuerzo–deformación, módulo de elasticidad y otras propiedades, exportación CSV/PDF/JPG.

## 3. Principios no negociables

1. **Rigor científico.** Nunca usar valores placeholder (como `0.0`) que parezcan datos reales. Si falta un dato, devolver `null`/`NaN` y registrar una advertencia en el resultado.
2. **Reproducibilidad.** Cada análisis guarda: parámetros (subset, search range, step), calibración, método de lectura de carga, hash del video y versión/commit del software.
3. **Geometría arbitraria.** Los nodos solo se ubican donde el subset completo cae dentro del objeto. La deformación se calcula sin depender de una grilla rectangular (triangulación o ventana local). Los nodos inválidos se marcan, no se fuerzan al borde.
4. **Unidades explícitas** (px, mm, N, MPa). La conversión px↔mm vive en un solo lugar (`dic/probeta.py`).
5. **Limitación 2D documentada.** Una cámara, plano del objeto perpendicular al eje óptico; el movimiento fuera del plano introduce error. No prometer mediciones 3D.
6. **Open source real.** Debe instalarse con `docker compose up` siguiendo el README, sin secretos en el repo, con licencia explícita y documentación en español e inglés **[DECIDIR: licencia e idioma]**.

## 4. Arquitectura objetivo

- **Estrategia por tipo de ensayo** (`dic/ensayos/`): una interfaz común que, para cada tipo (tracción, compresión, flexión, cortante, pórtico), define cómo se calcula el esfuerzo, qué magnitud mide el "extensómetro virtual" y cómo se obtiene el módulo. Agregar un ensayo nuevo no debe tocar el pipeline DIC.
- **Extensómetros virtuales:** longitud de calibración entre dos puntos (tracción/compresión), deflexión (flexión), deslizamiento relativo (conexiones) y rotación (pórticos).
- **Fuentes de carga** (`cargas/`):
  - Importador CSV/XLSX con mapeo de columnas y unidades.
  - OCR con recorte de ROI, que cuenta y reporta los fallos.
  - Sincronización temporal entre la carga y los frames (offset, evento de inicio, interpolación a los tiempos de frame).
- **Módulo de elasticidad:** ajuste lineal sobre un rango que el usuario elige según la norma aplicable. Se reporta el rango usado y el R². Nunca elegir el rango en silencio.
- **Subida de video:** endpoint con límite de tamaño y validación de extensión; el `source_id` de tipo archivo nunca acepta rutas arbitrarias del servidor.
- **Base de datos:** migraciones con Alembic. No agregar más columnas con `create_all`.

## 5. Reglas de trabajo para el agente

- Cambios pequeños y verificables. Correr `pytest` antes de dar una tarea por terminada.
- Idioma: código del dominio DIC, mensajes al usuario y documentación en español, como ya está en el repo.
- Frontend: usar **pnpm**; nunca `npm` ni `npx` (usar `pnpm exec`).
- No duplicar lógica: antes de agregar funciones sobre `dic/` vs `services/` (dispositivos, rastreo, análisis), eliminar la duplicación existente.
- No commitear `__pycache__`, `.expo/`, `.env`, videos de prueba ni contenido de `storage/`.
- Toda función DIC nueva lleva un test con datos sintéticos de desplazamiento conocido.
- **Preguntar antes de:** cambiar el algoritmo de correlación, el formato de resultados, el esquema de la base de datos, o agregar dependencias (revisar su licencia).
- No marcar una tarea como hecha si queda un `NotImplementedError`, un stub o un placeholder en su camino.

## 6. Validación (requisito para publicar)

- Carpeta `validation/` con scripts reproducibles.
- Imágenes sintéticas con desplazamiento y deformación conocidos (traslación rígida, estiramiento uniforme, gradiente): reportar error medio y desviación.
- Comparación contra extensómetro, LVDT o galga en ensayos reales.
- Documentar cuánta resolución de deformación se alcanza y con qué calidad de patrón speckle.

## 7. Prioridades (en orden)

1. Estabilizar la base: eliminar duplicados, Alembic, limpiar el repo, JWT y protección de endpoints, archivo `LICENSE`.
2. Subida de video y grabación desde el celular.
3. Geometría arbitraria: nodos válidos, máscara, deformación por triángulos o ventana local, mapas sobre la imagen.
4. Carga: importador de archivo + sincronización; OCR con ROI en la UI y manejo de fallos.
5. Resultados: gráficas, módulo de elasticidad y extensómetro virtual para tracción y compresión.
6. Exportación CSV/PDF/JPG con metadatos de reproducibilidad.
7. Validación y documentación para la conferencia.
8. Ensayos adicionales: flexión, cortante/conexiones, momento en pórticos.

## 8. Definición de "terminado"

- Los tests pasan y hay tests nuevos para lo agregado.
- Sin placeholders ni stubs en el flujo afectado.
- Migración incluida si cambió el esquema.
- README y `todo.md`/`plan.md` actualizados.
