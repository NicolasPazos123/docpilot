# DocPilot

Asistente RAG que responde preguntas sobre la documentación oficial de FastAPI, cita la sección exacta de donde sacó cada respuesta y tiene evals que miden su calidad.

## Estado

- [x] Fase 1: Fundamentos
- [ ] Fase 2: Ingesta (en progreso)
- [ ] Fase 3: Retrieval
- [ ] Fase 4: Generación con citas
- [ ] Fase 5: Evals
- [ ] Fase 6: Mejoras medidas
- [ ] Fase 7: Producción

## Stack

Python 3.12 · uv · Ollama (`nomic-embed-text`) · numpy

## Cómo correrlo

    uv sync
    ollama pull nomic-embed-text
    uv run python -m docpilot.demo_embeddings

    # Descargar el corpus (solo docs/en/docs del repo de FastAPI)
    git clone --depth 1 --filter=blob:none --sparse https://github.com/fastapi/fastapi.git data/fastapi
    git -C data/fastapi sparse-checkout set docs/en/docs

    # Cortar la documentación en chunks
    uv run python -m docpilot.ingesta

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
- **Pendiente:** 33 archivos no generan chunks (referencia de la API autogenerada, notas de versiones y páginas de la comunidad). Se van a excluir explícitamente, con su motivo.
