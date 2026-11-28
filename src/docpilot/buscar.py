import sys

from docpilot.db import conectar
from docpilot.indexar import embeber

K = 3  # cuántos chunks devolver


def buscar(pregunta: str, k: int = K) -> list[tuple[str, str, str, float]]:
    vector = embeber([pregunta], "search_query: ")[0]
    with conectar() as conexion:
        return conexion.execute(
            "SELECT ruta, url, texto, embedding <=> %s AS distancia "
            "FROM chunks ORDER BY distancia LIMIT %s",
            (vector, k),
        ).fetchall()


def main() -> None:
    if len(sys.argv) < 2:
        print('Uso: uv run python -m docpilot.buscar "tu pregunta"')
        return

    pregunta = " ".join(sys.argv[1:])
    print(f"Pregunta: {pregunta}\n")
    for i, (ruta, url, _texto, distancia) in enumerate(buscar(pregunta), start=1):
        print(f"{i}. {ruta}")
        print(f"   similitud: {1 - distancia:.3f}")
        print(f"   {url}\n")


if __name__ == "__main__":
    main()
