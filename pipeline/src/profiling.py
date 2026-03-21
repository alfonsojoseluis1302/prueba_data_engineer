"""Perfilado reutilizable de DataFrames."""

import pandas as pd
from datetime import datetime


def profile_dataframe(df: pd.DataFrame, table_name: str) -> dict:
    """Genera un perfil completo de un DataFrame."""
    total_rows = len(df)
    total_cols = len(df.columns)

    col_profiles = {}
    for col in df.columns:
        series = df[col]
        nulls = int(series.isna().sum())
        null_pct = round(nulls / total_rows * 100, 2) if total_rows > 0 else 0
        unique = int(series.nunique())

        profile = {
            "dtype": str(series.dtype),
            "nulls": nulls,
            "null_pct": null_pct,
            "unique": unique,
            "cardinality_pct": round(unique / total_rows * 100, 2) if total_rows > 0 else 0,
        }

        if pd.api.types.is_numeric_dtype(series):
            profile["min"] = series.min()
            profile["max"] = series.max()
            profile["mean"] = round(series.mean(), 2) if not series.isna().all() else None
            profile["median"] = round(series.median(), 2) if not series.isna().all() else None

        col_profiles[col] = profile

    # Duplicados por todas las columnas
    duplicated_rows = int(df.duplicated().sum())

    return {
        "table": table_name,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "duplicated_rows": duplicated_rows,
        "columns": col_profiles,
        "profiled_at": datetime.now().isoformat(),
    }


def detect_duplicates_by_key(df: pd.DataFrame, key_col: str) -> pd.DataFrame:
    """Retorna filas con PK duplicada."""
    dupes = df[df.duplicated(subset=[key_col], keep=False)]
    return dupes.sort_values(key_col)


def profile_to_markdown(profile: dict) -> str:
    """Convierte un perfil a markdown."""
    lines = [
        f"## Perfil: {profile['table']}",
        f"- **Filas:** {profile['total_rows']}",
        f"- **Columnas:** {profile['total_cols']}",
        f"- **Filas duplicadas (completas):** {profile['duplicated_rows']}",
        f"- **Perfilado:** {profile['profiled_at']}",
        "",
        "| Columna | Tipo | Nulos | %Nulos | Únicos | %Card |",
        "|---------|------|-------|--------|--------|-------|",
    ]
    for col, p in profile["columns"].items():
        lines.append(
            f"| {col} | {p['dtype']} | {p['nulls']} | {p['null_pct']}% "
            f"| {p['unique']} | {p['cardinality_pct']}% |"
        )
    return "\n".join(lines)
