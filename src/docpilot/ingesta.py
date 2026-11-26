import re
from dataclasses import dataclass
from pathlib import Path

DOCS_DIR = Path("data/fastapi/docs/en/docs")
BASE_URL = "https://fastapi.tiangolo.com"
PATRON_TITULO = re.compile(r"^(#{1,3}) (.+?) \{ #([\w-]+) \}\s*$", re.MULTILINE)


@dataclass
class Chunk:
    archivo: str
    titulo: str
    ancla: str
    url: str
    texto: str


def url_de(archivo: Path) -> str:
    partes = archivo.relative_to(DOCS_DIR).with_suffix("").parts
    if partes and partes[-1] == "index":
        partes = partes[:-1]
    camino = "/".join(partes)
    return f"{BASE_URL}/{camino}/" if camino else f"{BASE_URL}/"


def cortar_archivo(archivo: Path) -> list[Chunk]:
    contenido = archivo.read_text(encoding="utf-8")
    titulos = list(PATRON_TITULO.finditer(contenido))
    chunks = []
    for i, titulo in enumerate(titulos):
        inicio = titulo.end()
        fin = titulos[i + 1].start() if i + 1 < len(titulos) else len(contenido)
        texto = contenido[inicio:fin].strip()
        if not texto:
            continue
        chunks.append(
            Chunk(
                archivo=archivo.relative_to(DOCS_DIR).as_posix(),
                titulo=titulo.group(2),
                ancla=titulo.group(3),
                url=f"{url_de(archivo)}#{titulo.group(3)}",
                texto=texto,
            )
        )
    return chunks


def main() -> None:
    archivos = sorted(DOCS_DIR.rglob("*.md"))
    chunks: list[Chunk] = []
    sin_chunks: list[Path] = []
    for archivo in archivos:
        del_archivo = cortar_archivo(archivo)
        if not del_archivo:
            sin_chunks.append(archivo)
        chunks.extend(del_archivo)

    largos = [len(c.texto) for c in chunks]
    print(f"Archivos leídos: {len(archivos)}")
    print(f"Chunks creados: {len(chunks)}")
    print(f"Archivos sin chunks: {len(sin_chunks)}")
    print(f"Largo (caracteres): mín {min(largos)}, promedio {sum(largos) // len(largos)}, máx {max(largos)}")

    ejemplo = next(c for c in chunks if c.ancla == "create-your-data-model")
    print("\n--- Ejemplo de chunk ---")
    print(f"Archivo: {ejemplo.archivo}")
    print(f"Título:  {ejemplo.titulo}")
    print(f"URL:     {ejemplo.url}")
    print(f"Texto:\n{ejemplo.texto[:300]}…")


if __name__ == "__main__":
    main()