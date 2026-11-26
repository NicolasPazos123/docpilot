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
- **Hallazgo:** sin prefijos de tarea y con textos en español, los puntajes quedan muy apretados (0.52–0.60). Una frase sobre arroz (0.592) casi empata con la correcta (0.596).
- **Siguiente:** medir el efecto de los prefijos `search_query:` / `search_document:`.