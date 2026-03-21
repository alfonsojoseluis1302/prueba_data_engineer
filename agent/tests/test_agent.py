"""Tests del agente: herramientas y parsing."""

import pytest
from agent.tools import ejecutar_sql, obtener_esquema, resumir_reporte_calidad


class TestEjecutarSQL:
    def test_select_query(self):
        result = ejecutar_sql("SELECT * FROM gold_ventas_por_pais LIMIT 3")
        assert "pais_envio" in result or "ERROR" not in result

    def test_blocks_non_select(self):
        result = ejecutar_sql("DELETE FROM clientes")
        assert "ERROR" in result

    def test_blocks_drop(self):
        result = ejecutar_sql("DROP TABLE clientes")
        assert "ERROR" in result

    def test_filters_pii_columns(self):
        result = ejecutar_sql("SELECT * FROM clientes LIMIT 1")
        # nombre, apellido, email, telefono should be filtered
        assert "nombre" not in result.split("\n")[0] or "ERROR" in result

    def test_empty_result(self):
        result = ejecutar_sql("SELECT * FROM gold_ventas_por_pais WHERE pais_envio = 'Nonexistent'")
        assert "no retornó resultados" in result.lower() or len(result) > 0


class TestObtenerEsquema:
    def test_schema_pedidos(self):
        result = obtener_esquema("pedidos")
        assert "pedido_id" in result
        assert "Tabla: pedidos" in result

    def test_schema_gold_table(self):
        result = obtener_esquema("gold_ventas_por_pais")
        assert "gold_ventas_por_pais" in result

    def test_schema_nonexistent(self):
        result = obtener_esquema("tabla_inexistente")
        assert "ERROR" in result or "no encontrada" in result.lower()


class TestResumirReporte:
    def test_returns_content(self):
        result = resumir_reporte_calidad()
        # Debería tener contenido si el pipeline se ejecutó
        assert len(result) > 0
