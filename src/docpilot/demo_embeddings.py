import numpy as np
import ollama

MODELO = "nomic-embed-text"

pregunta = "¿Qué delantero mete más goles en la Champions?"
documentos = [
    "Haaland es un delantero noruego famoso por romper récords de goles.",
    "El VAR revisa las jugadas polémicas, como los fueras de juego.",
    "El Mundial 2026 se jugó en Estados Unidos, México y Canadá.",
    "Para el arroz con menestra hay que cocinar los fréjoles por horas.",
]


def embeber(textos: list[str], prefijo: str) -> np.ndarray:
    respuesta = ollama.embed(model=MODELO, input=[prefijo + t for t in textos])
    return np.array(respuesta.embeddings)


def similitud_coseno(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main() -> None:
    vec_pregunta = embeber([pregunta], "search_query: ")[0]
    vec_docs = embeber(documentos, "search_document: ")

    print(f"Cada embedding tiene {len(vec_pregunta)} dimensiones")
    print(f"Primeros 5 números de la pregunta: {vec_pregunta[:5].round(3)}\n")

    resultados = [(similitud_coseno(vec_pregunta, v), d) for v, d in zip(vec_docs, documentos)]
    for puntaje, doc in sorted(resultados, reverse=True):
        print(f"{puntaje:.3f}  {doc}")


if __name__ == "__main__":
    main()