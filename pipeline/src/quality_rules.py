"""Reglas de calidad formales para validación Silver."""

from dataclasses import dataclass
from typing import Callable
import pandas as pd


@dataclass
class QualityRule:
    rule_id: str
    table: str
    description: str
    severity: str  # "error" | "warning"
    check: Callable[[pd.DataFrame], pd.DataFrame]  # retorna filas que VIOLAN la regla


def _check_pk_unique(df: pd.DataFrame, pk_col: str) -> pd.DataFrame:
    return df[df.duplicated(subset=[pk_col], keep=False)]


def _check_not_null(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df[df[col].isna()]


def _check_not_value(df: pd.DataFrame, col: str, value: str) -> pd.DataFrame:
    return df[df[col] == value]


def _check_not_blank(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df[df[col].isna() | (df[col].astype(str).str.strip() == "")]


RULES = [
    QualityRule(
        rule_id="R001",
        table="clientes",
        description="PK cliente_id debe ser única",
        severity="error",
        check=lambda df: _check_pk_unique(df, "cliente_id"),
    ),
    QualityRule(
        rule_id="R002",
        table="pedidos",
        description="PK pedido_id debe ser única",
        severity="error",
        check=lambda df: _check_pk_unique(df, "pedido_id"),
    ),
    QualityRule(
        rule_id="R003",
        table="clientes",
        description="Email no debe ser nulo",
        severity="warning",
        check=lambda df: _check_not_null(df, "email"),
    ),
    QualityRule(
        rule_id="R004",
        table="clientes",
        description="Teléfono no debe ser 'N/A'",
        severity="warning",
        check=lambda df: _check_not_value(df, "telefono", "N/A"),
    ),
    QualityRule(
        rule_id="R005",
        table="clientes",
        description="Ciudad no debe ser vacía",
        severity="warning",
        check=lambda df: _check_not_blank(df, "ciudad"),
    ),
    QualityRule(
        rule_id="R006",
        table="productos",
        description="stock_disponible no debe ser nulo",
        severity="warning",
        check=lambda df: _check_not_null(df, "stock_disponible"),
    ),
    QualityRule(
        rule_id="R007",
        table="pedidos",
        description="FK cliente_id debe existir en clientes",
        severity="error",
        check=lambda df: pd.DataFrame(),  # se valida externamente con join
    ),
    QualityRule(
        rule_id="R008",
        table="productos",
        description="precio_venta > costo",
        severity="warning",
        check=lambda df: df[df["precio_venta"] <= df["costo"]],
    ),
    QualityRule(
        rule_id="R009",
        table="pedidos",
        description="total_neto consistente con total_bruto * (1 - descuento_pct)",
        severity="warning",
        check=lambda df: df[
            (df["total_bruto"].notna()) & (df["total_neto"].notna()) &
            (abs(df["total_neto"] - df["total_bruto"] * (1 - df["descuento_pct"])) > 1.0)
        ],
    ),
    QualityRule(
        rule_id="R010",
        table="pedidos",
        description="fecha_entrega >= fecha_pedido (cuando ambas existen)",
        severity="warning",
        check=lambda df: df[
            (df["fecha_entrega"].notna()) & (df["fecha_pedido"].notna()) &
            (df["fecha_entrega"] < df["fecha_pedido"])
        ],
    ),
    QualityRule(
        rule_id="R011",
        table="pedidos",
        description="estado en valores permitidos",
        severity="error",
        check=lambda df: df[
            ~df["estado"].isin(["pendiente", "enviado", "entregado", "cancelado", "devuelto"])
        ],
    ),
    QualityRule(
        rule_id="R012",
        table="eventos",
        description="PK evento_id debe ser única",
        severity="error",
        check=lambda df: _check_pk_unique(df, "evento_id"),
    ),
]


def validate_table(df: pd.DataFrame, table_name: str) -> list[dict]:
    """Ejecuta todas las reglas para una tabla y retorna resultados."""
    results = []
    table_rules = [r for r in RULES if r.table == table_name]
    for rule in table_rules:
        violations = rule.check(df)
        results.append({
            "rule_id": rule.rule_id,
            "table": table_name,
            "description": rule.description,
            "severity": rule.severity,
            "violations": len(violations),
            "passed": len(violations) == 0,
        })
    return results
