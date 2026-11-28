import time

import numpy as np
import ollama

from docpilot.db import conectar, crear_tabla
from docpilot.ingesta import cargar_chunks

MODELO = "nomic-embed-text"
TAMANO_LOTE = 32


def embeber(textos: list[str], prefijo: str) -> np.ndarray:
    respuesta = ollama.embed(model=MODELO, input=[prefijo + t for t in textos])
    return np.array(respuesta.embeddings)


def main() -> None:
    chunks = cargar_chunks()
    print(f"Chunks a indexar: {len(chunks)}")
    inicio = time.time()

    with conectar() as conexion:
        crear_tabla(conexion)
        conexion.execute("TRUNCATE chunks RESTART IDENTITY")

        for i in range(0, len(chunks), TAMANO_LOTE):
            lote = chunks[i : i + TAMANO_LOTE]
            vectores = embeber([c.texto_con_contexto for c in lote], "search_document: ")
            with conexion.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO chunks (archivo, titulo, ancla, url, ruta, texto, embedding) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    [(c.archivo, c.titulo, c.ancla, c.url, c.ruta, c.texto, v) for c, v in zip(lote, vectores)],
                )
            print(f"  {min(i + TAMANO_LOTE, len(chunks))}/{len(chunks)} chunks guardados")

        total = conexion.execute("SELECT count(*) FROM chunks").fetchone()[0]

    print(f"Listo: {total} chunks en la base, en {time.time() - inicio:.0f} segundos")


if __name__ == "__main__":
    main()
