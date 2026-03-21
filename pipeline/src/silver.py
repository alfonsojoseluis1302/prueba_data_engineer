"""Capa Silver: limpieza, validación, masking PII."""

import pandas as pd
from datetime import datetime

from pipeline.src.io_utils import (
    TABLES, SILVER_DIR, REPORTS_DIR, ensure_dirs, read_bronze, write_parquet, write_report,
)
from pipeline.src.profiling import profile_dataframe, profile_to_markdown
from pipeline.src.quality_rules import validate_table
from pipeline.src.cleaning import (
    fix_null_emails, fix_invalid_phones, fix_blank_cities,
    fix_null_stock, deduplicate_pedidos, fix_null_duracion,
)
from pipeline.src.masking import mask_clientes_pii


def _process_clientes(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    logs = []
    df, log = fix_null_emails(df)
    logs.append(log)
    df, log = fix_invalid_phones(df)
    logs.append(log)
    df, log = fix_blank_cities(df)
    logs.append(log)
    # Masking PII
    df = mask_clientes_pii(df)
    return df, logs


def _process_productos(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    logs = []
    df, log = fix_null_stock(df)
    logs.append(log)
    return df, logs


def _process_pedidos(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    logs = []
    df, log = deduplicate_pedidos(df)
    logs.append(log)
    return df, logs


def _process_detalle_pedidos(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    return df.copy(), []


def _process_eventos(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    logs = []
    df, log = fix_null_duracion(df)
    logs.append(log)
    return df, logs


PROCESSORS = {
    "clientes": _process_clientes,
    "productos": _process_productos,
    "pedidos": _process_pedidos,
    "detalle_pedidos": _process_detalle_pedidos,
    "eventos": _process_eventos,
}

# Orden FK: clientes → productos → pedidos → detalle_pedidos → eventos
PROCESSING_ORDER = ["clientes", "productos", "pedidos", "detalle_pedidos", "eventos"]


def run_silver() -> dict:
    """Ejecuta limpieza Silver para todas las tablas."""
    ensure_dirs()
    all_logs = []
    all_validations = []
    profiles = {}

    report_lines = [
        "# Reporte de Calidad — Capa Silver",
        f"**Generado:** {datetime.now().isoformat()}",
        "",
    ]

    for table in PROCESSING_ORDER:
        print(f"  [Silver] Processing {table}...")
        df = read_bronze(table)

        # Validar ANTES de limpiar
        pre_validation = validate_table(df, table)
        all_validations.extend(pre_validation)

        # Limpiar
        processor = PROCESSORS[table]
        df_clean, logs = processor(df)
        all_logs.extend(logs)

        # Validar DESPUÉS de limpiar
        post_validation = validate_table(df_clean, table)

        # Escribir parquet Silver
        write_parquet(df_clean, SILVER_DIR / f"{table}.parquet")

        # Perfil post-limpieza
        profile = profile_dataframe(df_clean, table)
        profiles[table] = profile

        report_lines.append(f"### {table}")
        report_lines.append("")

        # Mostrar correcciones aplicadas
        table_logs = [l for l in logs if l.get("registros_afectados", 0) > 0]
        if table_logs:
            report_lines.append("**Correcciones aplicadas:**")
            for log in table_logs:
                report_lines.append(
                    f"- `{log['campo']}`: {log['accion']} ({log['registros_afectados']} registros)"
                )
            report_lines.append("")

        # Mostrar validaciones
        report_lines.append("**Validaciones post-limpieza:**")
        report_lines.append("| Regla | Descripción | Violaciones | Estado |")
        report_lines.append("|-------|-------------|-------------|--------|")
        for v in post_validation:
            status = "PASS" if v["passed"] else "FAIL"
            report_lines.append(
                f"| {v['rule_id']} | {v['description']} | {v['violations']} | {status} |"
            )
        report_lines.append("")

        report_lines.append(profile_to_markdown(profile))
        report_lines.append("")

    write_report("\n".join(report_lines), "reporte_calidad_silver.md")

    # Log de transformaciones CSV
    if all_logs:
        log_df = pd.DataFrame(all_logs)
        log_df["timestamp"] = datetime.now().isoformat()
        log_path = REPORTS_DIR / "log_transformaciones.csv"
        log_df.to_csv(log_path, index=False)
        print(f"  [Silver] Log: {log_path}")

    print("  [Silver] Reporte generado: outputs/reports/reporte_calidad_silver.md")
    return profiles
