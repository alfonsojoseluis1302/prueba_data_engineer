"""Herramientas disponibles para el agente conversacional."""

import re
from pipeline.src.db_loader import get_connection, get_schema_for_table, list_tables
from pipeline.src.io_utils import REPORTS_DIR


# Tablas permitidas para el agente (Gold + Silver sin PII directa)
ALLOWED_TABLES = {
    "gold_ventas_por_pais", "gold_ventas_por_canal", "gold_ventas_mensuales",
    "gold_top_productos", "gold_segmento_clientes", "gold_conversion_funnel",
    "gold_clientes_rfm", "gold_resumen_calidad",
    "clientes", "productos", "pedidos", "detalle_pedidos", "eventos",
}

# Columnas PII que no deben exponerse en resultados
PII_COLUMNS = {"nombre", "apellido", "email", "telefono", "fecha_consentimiento"}


def ejecutar_sql(query: str) -> str:
    """Ejecuta una query SQL de solo lectura sobre las tablas Gold/Silver.

    Solo permite SELECT. Retorna resultados como texto tabular.
    """
    query = query.strip().rstrip(";")

    # Solo SELECT
    if not re.match(r"^\s*SELECT\b", query, re.IGNORECASE):
        return "ERROR: Solo se permiten consultas SELECT."

    # Bloquear operaciones peligrosas
    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE)\b",
        re.IGNORECASE,
    )
    if forbidden.search(query):
        return "ERROR: Operación no permitida. Solo consultas SELECT."

    try:
        con = get_connection()
        df = con.execute(query).fetchdf()
        con.close()

        # Filtrar columnas PII del resultado
        pii_found = [c for c in df.columns if c.lower() in PII_COLUMNS]
        if pii_found:
            df = df.drop(columns=pii_found)

        if len(df) == 0:
            return "La consulta no retornó resultados."

        # Limitar a 50 filas para el contexto del LLM
        if len(df) > 50:
            result = df.head(50).to_string(index=False)
            return f"{result}\n\n... (mostrando 50 de {len(df)} filas)"

        return df.to_string(index=False)
    except Exception as e:
        return f"ERROR SQL: {e}"


def obtener_esquema(tabla: str) -> str:
    """Retorna el esquema de una tabla desde el diccionario de datos."""
    # Mapear nombres gold a tablas base
    if tabla.startswith("gold_"):
        try:
            con = get_connection()
            cols = con.execute(f"DESCRIBE {tabla}").fetchdf()
            con.close()
            lines = [f"Tabla: {tabla}", ""]
            for _, row in cols.iterrows():
                lines.append(f"  - {row['column_name']}: {row['column_type']}")
            return "\n".join(lines)
        except Exception as e:
            return f"ERROR: No se pudo obtener esquema de '{tabla}': {e}"

    schema = get_schema_for_table(tabla)
    if not schema:
        return f"ERROR: Tabla '{tabla}' no encontrada en el diccionario de datos."

    lines = [f"Tabla: {tabla}", ""]
    for col in schema:
        pii_flag = " [PII-MASKED]" if col.get("es_pii") == "Sí" else ""
        lines.append(f"  - {col['columna']} ({col['tipo_dato']}): {col['descripcion']}{pii_flag}")
    return "\n".join(lines)


def resumir_reporte_calidad() -> str:
    """Retorna un resumen de los reportes de calidad del pipeline."""
    reports = []
    for filename in ["reporte_calidad_bronze.md", "reporte_calidad_silver.md", "reporte_calidad_gold.md"]:
        path = REPORTS_DIR / filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
            # Limitar tamaño para el contexto
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncado)"
            reports.append(f"## {filename}\n\n{content}")

    if not reports:
        return "No se encontraron reportes de calidad. Ejecute el pipeline primero."

    return "\n\n---\n\n".join(reports)


TOOLS_REGISTRY = {
    "ejecutar_sql": {
        "function": ejecutar_sql,
        "description": "Ejecuta una consulta SQL SELECT sobre las tablas de datos. "
                       "Tablas disponibles: gold_ventas_por_pais, gold_ventas_por_canal, "
                       "gold_ventas_mensuales, gold_top_productos, gold_segmento_clientes, "
                       "gold_conversion_funnel, gold_clientes_rfm, gold_resumen_calidad, "
                       "clientes, productos, pedidos, detalle_pedidos, eventos.",
        "parameters": {"query": "La consulta SQL a ejecutar (solo SELECT)"},
    },
    "obtener_esquema": {
        "function": obtener_esquema,
        "description": "Obtiene el esquema y descripción de columnas de una tabla.",
        "parameters": {"tabla": "Nombre de la tabla"},
    },
    "resumir_reporte_calidad": {
        "function": resumir_reporte_calidad,
        "description": "Retorna un resumen de los reportes de calidad del pipeline ETL.",
        "parameters": {},
    },
}
