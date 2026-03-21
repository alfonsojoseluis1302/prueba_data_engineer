"""Capa Bronze: ingesta raw → parquet con metadatos. Sin correcciones."""

import hashlib
import pandas as pd
from datetime import datetime

from pipeline.src.io_utils import (
    TABLES, RAW_DIR, BRONZE_DIR, ensure_dirs, read_raw, write_parquet, write_report,
)
from pipeline.src.profiling import profile_dataframe, profile_to_markdown


def _row_hash(row: pd.Series) -> str:
    """Genera un hash SHA-256 de la fila completa."""
    content = "|".join(str(v) for v in row.values)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def ingest_table(table: str) -> pd.DataFrame:
    """Ingesta una tabla raw a Bronze: agrega metadatos, escribe parquet."""
    df = read_raw(table)

    # Metadatos de auditoría
    df["_source_file"] = f"{table}.csv"
    df["_ingestion_timestamp"] = datetime.now().isoformat()
    df["_row_hash"] = df.apply(_row_hash, axis=1)

    # Tipado mínimo: fechas
    date_cols = [c for c in df.columns if "fecha" in c.lower()]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    write_parquet(df, BRONZE_DIR / f"{table}.parquet")
    return df


def run_bronze() -> dict:
    """Ejecuta ingesta Bronze para todas las tablas. Retorna perfiles."""
    ensure_dirs()
    profiles = {}
    report_lines = [
        "# Reporte de Calidad — Capa Bronze",
        f"**Generado:** {datetime.now().isoformat()}",
        "",
        "Bronze documenta el estado 'as-is' de los datos. No se aplican correcciones.",
        "",
    ]

    for table in TABLES:
        print(f"  [Bronze] Ingesting {table}...")
        df = ingest_table(table)
        profile = profile_dataframe(df, table)
        profiles[table] = profile
        report_lines.append(profile_to_markdown(profile))
        report_lines.append("")

    # Resumen de problemas detectados
    report_lines.append("## Problemas Detectados (sin corregir)")
    report_lines.append("")
    report_lines.append("| Tabla | Problema | Registros afectados |")
    report_lines.append("|-------|----------|---------------------|")

    for table, p in profiles.items():
        for col, cp in p["columns"].items():
            if cp["nulls"] > 0 and col not in ["_source_file", "_ingestion_timestamp", "_row_hash"]:
                report_lines.append(
                    f"| {table} | `{col}` nulos | {cp['nulls']} ({cp['null_pct']}%) |"
                )

    write_report("\n".join(report_lines), "reporte_calidad_bronze.md")
    print("  [Bronze] Reporte generado: outputs/reports/reporte_calidad_bronze.md")
    return profiles
