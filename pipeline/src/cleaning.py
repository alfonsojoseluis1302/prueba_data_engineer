"""Funciones de limpieza Silver. Cada una retorna (df_corregido, log_entry)."""

import pandas as pd


def fix_null_emails(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Reemplaza emails nulos con placeholder."""
    mask = df["email"].isna()
    count = int(mask.sum())
    df = df.copy()
    df.loc[mask, "email"] = "unknown@retailtech.co"
    return df, {
        "tabla": "clientes", "campo": "email", "accion": "null → 'unknown@retailtech.co'",
        "registros_afectados": count,
    }


def fix_invalid_phones(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Reemplaza teléfonos 'N/A' con None."""
    mask = df["telefono"] == "N/A"
    count = int(mask.sum())
    df = df.copy()
    df.loc[mask, "telefono"] = None
    return df, {
        "tabla": "clientes", "campo": "telefono", "accion": "'N/A' → null",
        "registros_afectados": count,
    }


def fix_blank_cities(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Reemplaza ciudades vacías/nulas con 'Desconocida'."""
    mask = df["ciudad"].isna() | (df["ciudad"].astype(str).str.strip() == "")
    count = int(mask.sum())
    df = df.copy()
    df.loc[mask, "ciudad"] = "Desconocida"
    return df, {
        "tabla": "clientes", "campo": "ciudad", "accion": "vacío → 'Desconocida'",
        "registros_afectados": count,
    }


def fix_null_stock(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Reemplaza stock nulo con 0."""
    mask = df["stock_disponible"].isna()
    count = int(mask.sum())
    df = df.copy()
    df.loc[mask, "stock_disponible"] = 0
    df["stock_disponible"] = df["stock_disponible"].astype(int)
    return df, {
        "tabla": "productos", "campo": "stock_disponible", "accion": "null → 0",
        "registros_afectados": count,
    }


def deduplicate_pedidos(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Elimina pedido_id duplicados, conserva la primera ocurrencia."""
    before = len(df)
    df = df.drop_duplicates(subset=["pedido_id"], keep="first").copy()
    removed = before - len(df)
    return df, {
        "tabla": "pedidos", "campo": "pedido_id", "accion": "deduplicación (keep first)",
        "registros_afectados": removed,
    }


def fix_null_duracion(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Reemplaza duracion_seg nula con la mediana por tipo_evento."""
    mask = df["duracion_seg"].isna()
    count = int(mask.sum())
    df = df.copy()
    medians = df.groupby("tipo_evento")["duracion_seg"].transform("median")
    df.loc[mask, "duracion_seg"] = medians[mask]
    # Si aún quedan nulos (tipo_evento sin datos), usar mediana global
    global_median = df["duracion_seg"].median()
    df["duracion_seg"] = df["duracion_seg"].fillna(global_median)
    return df, {
        "tabla": "eventos", "campo": "duracion_seg",
        "accion": "null → mediana por tipo_evento",
        "registros_afectados": count,
    }
