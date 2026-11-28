# DocPilot

Asistente RAG que responde preguntas sobre la documentación oficial de FastAPI, cita la sección exacta de donde sacó cada respuesta y tiene evals que miden su calidad.

## Estado

- [x] Fase 1: Fundamentos
- [x] Fase 2: Ingesta
- [ ] Fase 3: Retrieval (en progreso)
- [ ] Fase 4: Generación con citas
- [ ] Fase 5: Evals
- [ ] Fase 6: Mejoras medidas
- [ ] Fase 7: Producción

## Stack

Python 3.12 · uv · Ollama (`nomic-embed-text`) · numpy · Postgres 17 + pgvector (Docker Compose) · psycopg

## Cómo correrlo

    uv sync
    ollama pull nomic-embed-text
    uv run python -m docpilot.demo_embeddings

    # Descargar el corpus (solo docs/en/docs del repo de FastAPI)
    git clone --depth 1 --filter=blob:none --sparse https://github.com/fastapi/fastapi.git data/fastapi
    git -C data/fastapi sparse-checkout set docs/en/docs

    # Cortar la documentación en chunks
    uv run python -m docpilot.ingesta

    # Levantar Postgres con pgvector
    docker compose up -d

    # Calcular los embeddings y guardarlos en la base
    uv run python -m docpilot.indexar

    # Buscar
    uv run python -m docpilot.buscar "how do I read a cookie?"

## Bitácora

### Día 1: embeddings y búsqueda semántica

- Demo que convierte una pregunta y 4 frases en embeddings (768 dimensiones) y las ordena por similitud coseno.
- **Experimento: prefijos de tarea** (`search_query:` / `search_document:`) en `nomic-embed-text`:

| | Correcto (Haaland) | Mejor incorrecto (arroz) | Margen |
|---|---|---|---|
| Sin prefijos | 0.596 | 0.592 | 0.004 |
| Con prefijos | 0.637 | 0.599 | **0.038 (~10x)** |

- **Conclusión:** los prefijos mejoran mucho la separación, pero en español el modelo sigue confundiendo el ranking (el arroz queda 2.º). Hipótesis: el modelo se entrenó sobre todo en inglés. A DocPilot no le afecta (la documentación de FastAPI está en inglés).

- **Experimento: idioma** (mismas frases, con prefijos):

| Idioma | Correcto (Haaland) | 2.º lugar | Margen | Arroz (irrelevante) |
|---|---|---|---|---|
| Español | 0.637 | 0.599 (arroz) | 0.038 | 2.º |
| Inglés | 0.673 | 0.450 (VAR) | **0.223 (~6x)** | último |

- **Conclusión:** hipótesis confirmada: `nomic-embed-text` rinde mucho mejor en inglés. Decisión pendiente para la fase 6: preguntas en español sobre documentación en inglés (modelo multilingüe o traducir la consulta), a decidir midiendo.

### Día 2: ingesta y chunking

- **Corpus:** 159 archivos Markdown de la documentación oficial (`docs/en/docs` del repo de FastAPI). Se descargan con sparse checkout en lugar de hacer scraping del sitio web: el Markdown es la fuente limpia y no trae menús ni HTML.
- **Chunking por estructura:** se corta en los títulos con ancla `{ #ancla }`, que además dan la URL exacta para citar (por ejemplo `https://fastapi.tiangolo.com/tutorial/body/#create-your-data-model`).
- **Experimento: cortar también en `###`:**

| | Chunks | Mín | Promedio | Máx |
|---|---|---|---|---|
| `#` y `##` | 719 | 49 | 1005 | 18 356 |
| `#`, `##` y `###` | 1075 | 6 | 651 | 6 203 |

- **Conclusión:** se adopta `###`. Las secciones con muchos subtemas (por ejemplo "Previous tools", con 17 herramientas) dejan de quedar en un solo chunk: un chunk = un tema. Costo: aparecen chunks muy pequeños (mín. 6 caracteres), a resolver en la limpieza.
- **Exclusiones a propósito:** 33 archivos se excluyen explícitamente, cada uno con su motivo en `EXCLUSIONES` (`ingesta.py`):
  - `reference/` (24 archivos): la referencia de la API se genera desde el código fuente; el `.md` no trae el contenido.
  - `release-notes.md`: historial de versiones, ruido para preguntas de "cómo hago X".
  - Fragmentos que se insertan en otras páginas (`agent-banner.md`, `translation-banner.md`) y páginas sobre el proyecto (`contributing.md`, `fastapi-people.md`, etc.).
- **Resultado:** 126 archivos procesados → 1075 chunks · 33 excluidos a propósito · **0 archivos sin chunks inesperados** (alarma de diagnóstico).
- **Limpieza** (función `limpiar`, aplicada a cada chunk):
  - Se quitan las marcas del sitio: huecos de código `{* ... *}`, marcos de notas `///` (también indentados), `<img>`, `<abbr>` y comentarios HTML `<!-- -->`.
  - Se quitan los links de Markdown de los títulos: `[Flask](https://...)` → `Flask`.
  - Control de calidad: se cuentan los chunks que aún contienen alguna marca, usando los mismos patrones de limpieza → **0**.
  - Se excluyó además `_llm-test.md` (archivo interno de pruebas de FastAPI).
- **Ruta de títulos** (*contextual chunk headers*): cada chunk guarda el camino de títulos que tiene encima, por ejemplo `Alternatives, Inspiration and Comparisons > Previous tools > Flask`. Para el embedding se usa `ruta + texto`, así un chunk de `###` no pierde el contexto de su sección.
- **Chunks chicos:** los chunks de menos de 150 caracteres se juntan con el anterior del mismo archivo (manteniendo la cita del anterior). Quedan 22 chicos que son la introducción de su archivo y no tienen anterior.

| Paso | Chunks | Mín | Promedio | Máx |
|---|---|---|---|---|
| Corte en `#`, `##`, `###` | 1075 | 6 | 651 | 6 203 |
| + limpieza y exclusiones | 1055 | 22 | 608 | 6 148 |
| + juntar chunks chicos | **943** | **36** | **683** | **6 148** |

### Día 3: base de datos vectorial y primera búsqueda

- **Postgres 17 + pgvector 0.8.7** en Docker Compose (`docker-compose.yml`), con un volumen (`pgdata`) para que los datos sobrevivan si se recrea el contenedor. Puerto 5433 en el host para no chocar con otros Postgres.
- **Tabla `chunks`:** `archivo`, `titulo`, `ancla`, `url`, `ruta`, `texto` y `embedding vector(768)`.
- **Indexación** (`indexar.py`): 943 chunks → embeddings de `ruta + texto` con el prefijo `search_document:`, por lotes de 32. **83 segundos** en una Mac M1. Es idempotente (`TRUNCATE` antes de insertar).
- **Búsqueda** (`buscar.py`): la pregunta se convierte en embedding con `search_query:` y se ordena por distancia coseno (`<=>`) en SQL.
- **Primeras pruebas:**

| Pregunta | Top 1 | Similitud top 1 | Margen 1.º–2.º |
|---|---|---|---|
| how do I deploy FastAPI with Docker? | Docker > Deploy the Container Image | 0.872 | 0.003 (los 3 son de `docker.md`) |
| how do I read a cookie? | Cookie Parameter Models > Check the Docs | 0.698 | 0.002 |
| ¿cómo leo una cookie? | Cookie Parameters > Declare `Cookie` parameters | 0.588 | 0.000 |

- **Hallazgos:** el retrieval encuentra bien el **tema**, pero el **orden dentro del tema** es frágil: en la pregunta de cookies, la mejor sección quedó 2.ª y el 3.º resultado trata de *enviar* cookies, no de leerlas. En español la similitud cae (0.698 → 0.588), lo que confirma el efecto del idioma del Día 1.
- **Siguiente:** medir esto con un dataset de preguntas (fase 5) y probar re-ranking (fase 6).
