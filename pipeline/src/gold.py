"""Capa Gold: tablas analíticas agregadas."""

import pandas as pd
import numpy as np
from datetime import datetime

from pipeline.src.io_utils import (
    GOLD_DIR, ensure_dirs, read_silver, write_parquet, write_report,
)
from pipeline.src.db_loader import get_connection, load_df_to_table
from pipeline.src.profiling import profile_dataframe, profile_to_markdown


def _load_silver_tables() -> dict[str, pd.DataFrame]:
    """Carga todas las tablas Silver."""
    tables = {}
    for name in ["clientes", "productos", "pedidos", "detalle_pedidos", "eventos"]:
        tables[name] = read_silver(name)
    return tables


def gold_ventas_por_pais(pedidos: pd.DataFrame) -> pd.DataFrame:
    """Revenue por país."""
    return (
        pedidos.groupby("pais_envio")
        .agg(
            total_pedidos=("pedido_id", "count"),
            revenue_bruto=("total_bruto", "sum"),
            revenue_neto=("total_neto", "sum"),
            ticket_promedio=("total_neto", "mean"),
        )
        .reset_index()
        .sort_values("revenue_neto", ascending=False)
    )


def gold_ventas_por_canal(pedidos: pd.DataFrame) -> pd.DataFrame:
    """Revenue por canal de venta."""
    return (
        pedidos.groupby("canal")
        .agg(
            total_pedidos=("pedido_id", "count"),
            revenue_neto=("total_neto", "sum"),
            descuento_promedio=("descuento_pct", "mean"),
        )
        .reset_index()
        .sort_values("revenue_neto", ascending=False)
    )


def gold_ventas_mensuales(pedidos: pd.DataFrame) -> pd.DataFrame:
    """Serie temporal de ventas mensuales."""
    df = pedidos.copy()
    df["mes"] = pd.to_datetime(df["fecha_pedido"]).dt.to_period("M").astype(str)
    return (
        df.groupby("mes")
        .agg(
            total_pedidos=("pedido_id", "count"),
            revenue_neto=("total_neto", "sum"),
        )
        .reset_index()
        .sort_values("mes")
    )


def gold_top_productos(detalle: pd.DataFrame, productos: pd.DataFrame) -> pd.DataFrame:
    """Top productos por ingreso."""
    merged = detalle.merge(
        productos[["producto_id", "nombre_producto", "categoria", "subcategoria"]],
        on="producto_id", how="left",
    )
    return (
        merged.groupby(["producto_id", "nombre_producto", "categoria", "subcategoria"])
        .agg(
            unidades_vendidas=("cantidad", "sum"),
            revenue=("subtotal", "sum"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )


def gold_segmento_clientes(pedidos: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    """Análisis por segmento de clientes."""
    merged = pedidos.merge(
        clientes[["cliente_id", "segmento", "pais"]],
        on="cliente_id", how="left",
    )
    return (
        merged.groupby("segmento")
        .agg(
            total_clientes=("cliente_id", "nunique"),
            total_pedidos=("pedido_id", "count"),
            revenue_neto=("total_neto", "sum"),
            ticket_promedio=("total_neto", "mean"),
        )
        .reset_index()
    )


def gold_conversion_funnel(eventos: pd.DataFrame) -> pd.DataFrame:
    """Funnel de conversión digital."""
    funnel_order = ["page_view", "product_view", "add_to_cart", "checkout", "purchase"]
    counts = eventos.groupby("tipo_evento")["evento_id"].count().reset_index()
    counts.columns = ["tipo_evento", "total_eventos"]
    # Solo eventos del funnel
    funnel = counts[counts["tipo_evento"].isin(funnel_order)].copy()
    funnel["orden"] = funnel["tipo_evento"].map({e: i for i, e in enumerate(funnel_order)})
    funnel = funnel.sort_values("orden").drop(columns=["orden"])
    # Tasa de conversión respecto al paso anterior
    funnel["conversion_rate"] = funnel["total_eventos"].pct_change().fillna(0).round(4)
    return funnel.reset_index(drop=True)


def gold_clientes_rfm(pedidos: pd.DataFrame) -> pd.DataFrame:
    """Segmentación RFM (con IDs masked — ya vienen de Silver)."""
    ref_date = pd.to_datetime(pedidos["fecha_pedido"]).max() + pd.Timedelta(days=1)
    df = pedidos.copy()
    df["fecha_pedido"] = pd.to_datetime(df["fecha_pedido"])

    rfm = (
        df.groupby("cliente_id")
        .agg(
            recency=("fecha_pedido", lambda x: (ref_date - x.max()).days),
            frequency=("pedido_id", "count"),
            monetary=("total_neto", "sum"),
        )
        .reset_index()
    )

    # Scoring RFM (1-5)
    for col in ["recency", "frequency", "monetary"]:
        ascending = col == "recency"  # menor recency = mejor
        rfm[f"{col}_score"] = pd.qcut(
            rfm[col].rank(method="first"), q=5, labels=[5, 4, 3, 2, 1] if ascending else [1, 2, 3, 4, 5]
        ).astype(int)

    rfm["rfm_score"] = (
        rfm["recency_score"].astype(str)
        + rfm["frequency_score"].astype(str)
        + rfm["monetary_score"].astype(str)
    )
    return rfm


def gold_resumen_calidad(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Resumen de calidad para el agente."""
    rows = []
    for name, df in tables.items():
        total = len(df)
        nulls = int(df.isna().sum().sum())
        rows.append({
            "tabla": name,
            "total_filas": total,
            "total_columnas": len(df.columns),
            "total_nulos": nulls,
            "pct_completitud": round((1 - nulls / (total * len(df.columns))) * 100, 2) if total > 0 else 0,
        })
    return pd.DataFrame(rows)


def run_gold() -> dict:
    """Ejecuta generación de tablas Gold."""
    ensure_dirs()
    tables = _load_silver_tables()

    gold_tables = {}

    print("  [Gold] Generando tablas analíticas...")

    gold_tables["gold_ventas_por_pais"] = gold_ventas_por_pais(tables["pedidos"])
    gold_tables["gold_ventas_por_canal"] = gold_ventas_por_canal(tables["pedidos"])
    gold_tables["gold_ventas_mensuales"] = gold_ventas_mensuales(tables["pedidos"])
    gold_tables["gold_top_productos"] = gold_top_productos(tables["detalle_pedidos"], tables["productos"])
    gold_tables["gold_segmento_clientes"] = gold_segmento_clientes(tables["pedidos"], tables["clientes"])
    gold_tables["gold_conversion_funnel"] = gold_conversion_funnel(tables["eventos"])
    gold_tables["gold_clientes_rfm"] = gold_clientes_rfm(tables["pedidos"])
    gold_tables["gold_resumen_calidad"] = gold_resumen_calidad(tables)

    # Escribir parquets y cargar en DuckDB
    con = get_connection()
    for name, df in gold_tables.items():
        write_parquet(df, GOLD_DIR / f"{name}.parquet")
        load_df_to_table(con, name, df)
        print(f"    → {name}: {len(df)} filas")

    # También cargar Silver en DuckDB para queries
    for name, df in tables.items():
        load_df_to_table(con, name, df)

    con.close()

    # Reporte
    report_lines = [
        "# Reporte de Calidad — Capa Gold",
        f"**Generado:** {datetime.now().isoformat()}",
        "",
        "## Tablas Generadas",
        "",
        "| Tabla | Filas | Columnas |",
        "|-------|-------|----------|",
    ]
    for name, df in gold_tables.items():
        report_lines.append(f"| {name} | {len(df)} | {len(df.columns)} |")

    report_lines.append("")
    report_lines.append("## Resumen de Calidad Silver (input)")
    report_lines.append("")
    report_lines.append(gold_tables["gold_resumen_calidad"].to_markdown(index=False))

    write_report("\n".join(report_lines), "reporte_calidad_gold.md")
    print("  [Gold] Reporte generado: outputs/reports/reporte_calidad_gold.md")
    return gold_tables
