import psycopg
from pgvector.psycopg import register_vector

DB_URL = "postgresql://docpilot:docpilot@localhost:5433/docpilot"
DIMENSIONES = 768


def conectar() -> psycopg.Connection:
    conexion = psycopg.connect(DB_URL, autocommit=True)
    conexion.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conexion)
    return conexion


def crear_tabla(conexion: psycopg.Connection) -> None:
    conexion.execute(
        f"""
        CREATE TABLE IF NOT EXISTS chunks (
            id SERIAL PRIMARY KEY,
            archivo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            ancla TEXT NOT NULL,
            url TEXT NOT NULL,
            ruta TEXT NOT NULL,
            texto TEXT NOT NULL,
            embedding vector({DIMENSIONES}) NOT NULL
        )
        """
    )


def main() -> None:
    with conectar() as conexion:
        crear_tabla(conexion)
        version = conexion.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()[0]
        filas = conexion.execute("SELECT count(*) FROM chunks").fetchone()[0]
        print(f"Conectado. pgvector {version}. Tabla chunks lista con {filas} filas.")


if __name__ == "__main__":
    main()