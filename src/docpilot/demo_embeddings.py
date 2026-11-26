import numpy as np
import ollama

MODELO = "nomic-embed-text"

CASOS = {
    "español": (
        "¿Qué delantero mete más goles en la Champions?",
        [
            "Haaland es un delantero noruego famoso por romper récords de goles.",
            "El VAR revisa las jugadas polémicas, como los fueras de juego.",
            "El Mundial 2026 se jugó en Estados Unidos, México y Canadá.",
            "Para el arroz con menestra hay que cocinar los fréjoles por horas.",
        ],
    ),
    "inglés": (
        "Which striker scores the most goals in the Champions League?",
        [
            "Haaland is a Norwegian striker famous for breaking goal-scoring records.",
            "VAR reviews controversial plays, such as offside calls.",
            "The 2026 World Cup was played in the United States, Mexico and Canada.",
            "To make rice and beans, you have to cook the beans for hours.",
        ],
    ),
}


def embeber(textos: list[str], prefijo: str) -> np.ndarray:
    respuesta = ollama.embed(model=MODELO, input=[prefijo + t for t in textos])
    return np.array(respuesta.embeddings)


def similitud_coseno(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def buscar(pregunta: str, documentos: list[str]) -> list[tuple[float, str]]:
    vec_pregunta = embeber([pregunta], "search_query: ")[0]
    vec_docs = embeber(documentos, "search_document: ")
    resultados = [(similitud_coseno(vec_pregunta, v), d) for v, d in zip(vec_docs, documentos)]
    return sorted(resultados, reverse=True)


def main() -> None:
    for idioma, (pregunta, documentos) in CASOS.items():
        print(f"\n=== {idioma} ===")
        ranking = buscar(pregunta, documentos)
        for puntaje, doc in ranking:
            print(f"{puntaje:.3f}  {doc}")
        margen = ranking[0][0] - ranking[1][0]
        print(f"Margen (1.º - 2.º): {margen:.3f}")


if __name__ == "__main__":
    main()