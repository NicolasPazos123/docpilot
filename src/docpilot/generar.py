import sys

from dotenv import load_dotenv
from groq import Groq

from docpilot.buscar import buscar

MODELO_LLM = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """Eres DocPilot, un asistente que responde preguntas sobre la documentación oficial de FastAPI.

Reglas:
- Responde en español, de forma clara y breve.
- Usa SOLO la información del contexto. No uses conocimiento propio.
- Cita cada afirmación con el número de su fuente entre corchetes, por ejemplo [1].
- Si el contexto no alcanza para responder, dilo claramente en lugar de inventar."""


def armar_contexto(resultados: list[tuple[str, str, str, float]]) -> str:
    bloques = []
    for i, (ruta, url, texto, _distancia) in enumerate(resultados, start=1):
        bloques.append(f"[{i}] {ruta}\nURL: {url}\n{texto}")
    return "\n\n---\n\n".join(bloques)


def responder(pregunta: str) -> tuple[str, list[tuple[str, str, str, float]]]:
    resultados = buscar(pregunta)
    contexto = armar_contexto(resultados)
    cliente = Groq()
    respuesta = cliente.chat.completions.create(
        model=MODELO_LLM,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Contexto:\n\n{contexto}\n\nPregunta: {pregunta}"},
        ],
    )
    return respuesta.choices[0].message.content, resultados


def main() -> None:
    load_dotenv()
    if len(sys.argv) < 2:
        print('Uso: uv run python -m docpilot.generar "tu pregunta"')
        return

    pregunta = " ".join(sys.argv[1:])
    texto, resultados = responder(pregunta)

    print(f"Pregunta: {pregunta}\n")
    print(texto)
    print("\nFuentes:")
    for i, (ruta, url, _texto, distancia) in enumerate(resultados, start=1):
        print(f"  [{i}] {ruta} (similitud {1 - distancia:.3f})")
        print(f"      {url}")


if __name__ == "__main__":
    main()
