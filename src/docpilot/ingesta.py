import re
from dataclasses import dataclass
from pathlib import Path

DOCS_DIR = Path("data/fastapi/docs/en/docs")
BASE_URL = "https://fastapi.tiangolo.com"
PATRON_TITULO = re.compile(r"^(#{1,3}) (.+?) \{ #([\w-]+) \}\s*$", re.MULTILINE)

EXCLUSIONES = {
    "reference/": "Referencia de la API: se genera desde el código fuente, el .md no trae el contenido",
    "release-notes.md": "Historial de versiones: ruido para preguntas de cómo hacer algo",
    "agent-banner.md": "Fragmento que se inserta dentro de otras páginas",
    "translation-banner.md": "Fragmento que se inserta dentro de otras páginas",
    "contributing.md": "Página sobre el proyecto, no sobre cómo usar FastAPI",
    "external-links.md": "Página sobre el proyecto, no sobre cómo usar FastAPI",
    "fastapi-people.md": "Página sobre el proyecto, no sobre cómo usar FastAPI",
    "management.md": "Página sobre el proyecto, no sobre cómo usar FastAPI",
    "newsletter.md": "Página sobre el proyecto, no sobre cómo usar FastAPI",
    "translations.md": "Página sobre el proyecto, no sobre cómo usar FastAPI",
    "_llm-test.md": "Archivo interno de pruebas de FastAPI, no es documentación",
}

PATRON_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")  # [Flask](https://...) -> Flask

PATRONES_LIMPIEZA = [
    (re.compile(r"^[ \t]*\{\*.*\*\}\s*$", re.MULTILINE), ""),  # {* ../../docs_src/... *}
    (re.compile(r"^[ \t]*///.*$", re.MULTILINE), ""),  # /// note, /// tip, ///
    (re.compile(r"<img[^>]*>"), ""),  # <img src="...">
    (re.compile(r"</?abbr[^>]*>"), ""),  # <abbr title="...">UIs</abbr> -> UIs
    (re.compile(r"<!--.*?-->", re.DOTALL), ""),  # <!-- comentarios HTML -->
    (re.compile(r"\n{3,}"), "\n\n"),  # líneas en blanco de sobra
]


@dataclass
class Chunk:
    archivo: str
    titulo: str
    ancla: str
    url: str
    texto: str


def motivo_exclusion(ruta: str) -> str | None:
    for patron, motivo in EXCLUSIONES.items():
        if ruta == patron or (patron.endswith("/") and ruta.startswith(patron)):
            return motivo
    return None


def limpiar(texto: str) -> str:
    for patron, reemplazo in PATRONES_LIMPIEZA:
        texto = patron.sub(reemplazo, texto)
    return texto.strip()


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
        texto = limpiar(contenido[inicio:fin])
        if not texto:
            continue
        chunks.append(
            Chunk(
                archivo=archivo.relative_to(DOCS_DIR).as_posix(),
                titulo=PATRON_LINK.sub(r"\1", titulo.group(2)),
                ancla=titulo.group(3),
                url=f"{url_de(archivo)}#{titulo.group(3)}",
                texto=texto,
            )
        )
    return chunks


def main() -> None:
    archivos = sorted(DOCS_DIR.rglob("*.md"))
    chunks: list[Chunk] = []
    excluidos: list[tuple[str, str]] = []
    sin_chunks: list[str] = []
    for archivo in archivos:
        ruta = archivo.relative_to(DOCS_DIR).as_posix()
        motivo = motivo_exclusion(ruta)
        if motivo:
            excluidos.append((ruta, motivo))
            continue
        del_archivo = cortar_archivo(archivo)
        if not del_archivo:
            sin_chunks.append(ruta)
        chunks.extend(del_archivo)

    largos = [len(c.texto) for c in chunks]
    con_marcas = [c for c in chunks if any(p.search(c.texto) for p, _ in PATRONES_LIMPIEZA[:-1])]
    print(f"Archivos leídos: {len(archivos)}")
    print(f"Archivos excluidos a propósito: {len(excluidos)}")
    print(f"Archivos sin chunks (inesperado): {len(sin_chunks)}")
    for ruta in sin_chunks:
        print(f"  ⚠️ {ruta}")
    print(f"Chunks creados: {len(chunks)}")
    print(f"Chunks con marcas sin limpiar: {len(con_marcas)}")
    print(f"Largo (caracteres): mín {min(largos)}, promedio {sum(largos) // len(largos)}, máx {max(largos)}")


if __name__ == "__main__":
    main()