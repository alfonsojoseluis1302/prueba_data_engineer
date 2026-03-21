"""Conexión y utilidades DuckDB."""

import duckdb
import pandas as pd
from pipeline.src.io_utils import DUCKDB_PATH, load_diccionario


def get_connection() -> duckdb.DuckDBPyConnection:
    """Retorna una conexión a la base DuckDB del proyecto."""
    return duckdb.connect(str(DUCKDB_PATH))


def register_df(con: duckdb.DuckDBPyConnection, name: str, df: pd.DataFrame):
    """Registra un DataFrame como tabla en DuckDB."""
    con.register(name, df)


def execute_query(con: duckdb.DuckDBPyConnection, query: str) -> pd.DataFrame:
    """Ejecuta una query y retorna un DataFrame."""
    return con.execute(query).fetchdf()


def load_df_to_table(con: duckdb.DuckDBPyConnection, name: str, df: pd.DataFrame):
    """Crea o reemplaza una tabla persistente en DuckDB desde un DataFrame."""
    con.register("_tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM _tmp_df")
    con.unregister("_tmp_df")


def get_schema_for_table(table_name: str) -> list[dict]:
    """Retorna el esquema de una tabla desde el diccionario de datos."""
    dic = load_diccionario()
    rows = dic[dic["tabla"] == table_name]
    return rows.to_dict(orient="records")


def list_tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Lista todas las tablas registradas en DuckDB."""
    result = con.execute("SHOW TABLES").fetchdf()
    return result["name"].tolist()
