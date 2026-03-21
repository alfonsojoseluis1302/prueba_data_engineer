"""Rutas centralizadas y utilidades de lectura/escritura."""

from pathlib import Path
import pandas as pd

# ── Directorios base ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
DATA_DIR = PIPELINE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

REPORTS_DIR = PIPELINE_DIR / "outputs" / "reports"
QUERIES_DIR = PIPELINE_DIR / "outputs" / "queries"
DUCKDB_PATH = DATA_DIR / "retailtech.duckdb"

# Tablas fuente
TABLES = ["clientes", "productos", "pedidos", "detalle_pedidos", "eventos"]


def ensure_dirs():
    """Crea directorios de salida si no existen."""
    for d in [BRONZE_DIR, SILVER_DIR, GOLD_DIR, REPORTS_DIR, QUERIES_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    """Lee un CSV con encoding utf-8."""
    return pd.read_csv(path, encoding="utf-8", **kwargs)


def read_raw(table: str) -> pd.DataFrame:
    """Lee una tabla desde la capa raw."""
    return read_csv(RAW_DIR / f"{table}.csv")


def read_parquet(path: Path) -> pd.DataFrame:
    """Lee un archivo Parquet."""
    return pd.read_parquet(path)


def write_parquet(df: pd.DataFrame, path: Path):
    """Escribe un DataFrame a Parquet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow")


def read_bronze(table: str) -> pd.DataFrame:
    return read_parquet(BRONZE_DIR / f"{table}.parquet")


def read_silver(table: str) -> pd.DataFrame:
    return read_parquet(SILVER_DIR / f"{table}.parquet")


def read_gold(table: str) -> pd.DataFrame:
    return read_parquet(GOLD_DIR / f"{table}.parquet")


def load_diccionario() -> pd.DataFrame:
    """Carga el diccionario de datos."""
    return read_csv(RAW_DIR / "diccionario_datos.csv")


def write_report(content: str, filename: str):
    """Escribe un reporte markdown."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / filename).write_text(content, encoding="utf-8")
