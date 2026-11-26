# DocPilot

Asistente RAG que responde preguntas sobre la documentación oficial de FastAPI, cita la sección exacta de donde sacó cada respuesta y tiene evals que miden su calidad.

## Estado

- [ ] Fase 1: Fundamentos (en progreso)
- [ ] Fase 2: Ingesta
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

## Bitácora

### Día 1: embeddings y búsqueda semántica

- Demo que convierte una pregunta y 4 frases en embeddings (768 dimensiones) y las ordena por similitud coseno.
- **Experimento: prefijos de tarea** (`search_query:` / `search_document:`) en `nomic-embed-text`:

| | Correcto (Haaland) | Mejor incorrecto (arroz) | Margen |
|---|---|---|---|
| Sin prefijos | 0.596 | 0.592 | 0.004 |
| Con prefijos | 0.637 | 0.599 | **0.038 (~10x)** |

- **Conclusión:** los prefijos mejoran mucho la separación, pero en español el modelo sigue confundiendo el ranking (el arroz queda 2.º). Hipótesis: el modelo se entrenó sobre todo en inglés. A DocPilot no le afecta (la documentación de FastAPI está en inglés).