"""Parser y ejecutor de queries SQL nombradas."""

import re
import pandas as pd
from pathlib import Path
from pipeline.src.io_utils import QUERIES_DIR, PIPELINE_DIR, ensure_dirs
from pipeline.src.db_loader import get_connection


QUERIES_FILE = PIPELINE_DIR / "queries.sql"


def parse_queries(sql_file: Path = QUERIES_FILE) -> dict[str, str]:
    """Parsea queries nombradas desde un archivo SQL.

    Formato esperado:
        -- @name: q01_nombre
        -- Descripción
        SELECT ...;
    """
    content = sql_file.read_text(encoding="utf-8")
    queries = {}
    current_name = None
    current_lines = []

    for line in content.split("\n"):
        name_match = re.match(r"--\s*@name:\s*(\S+)", line)
        if name_match:
            # Guardar query anterior
            if current_name and current_lines:
                queries[current_name] = "\n".join(current_lines).strip()
            current_name = name_match.group(1)
            current_lines = []
        else:
            if current_name is not None:
                current_lines.append(line)

    # Última query
    if current_name and current_lines:
        queries[current_name] = "\n".join(current_lines).strip()

    return queries


def run_queries():
    """Ejecuta todas las queries y exporta resultados a CSV."""
    ensure_dirs()
    queries = parse_queries()
    con = get_connection()

    print(f"  [Queries] Ejecutando {len(queries)} queries...")

    for name, sql in queries.items():
        # Filtrar líneas que son solo comentarios, luego limpiar
        lines = [l for l in sql.split("\n") if not l.strip().startswith("--")]
        clean_sql = "\n".join(lines).strip().rstrip(";").strip()
        if not clean_sql:
            continue

        try:
            df = con.execute(clean_sql).fetchdf()
            output_path = QUERIES_DIR / f"{name}.csv"
            df.to_csv(output_path, index=False)
            print(f"    → {name}: {len(df)} filas → {output_path.name}")
        except Exception as e:
            print(f"    ✗ {name}: ERROR - {e}")

    con.close()
    print("  [Queries] Completado.")
