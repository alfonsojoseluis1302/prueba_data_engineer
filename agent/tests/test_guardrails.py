"""Tests de guardrails: detección y filtrado de PII."""

import pytest
from agent.guardrails import detect_pii, sanitize_output, validate_query_safety


class TestDetectPII:
    def test_detects_email(self):
        findings = detect_pii("El email es juan.perez@gmail.com y ya.")
        assert any(f["type"] == "email" for f in findings)

    def test_ignores_safe_emails(self):
        findings = detect_pii("Contactar a crm@retailtech.co")
        assert not any(f["type"] == "email" for f in findings)

    def test_no_pii_in_clean_text(self):
        findings = detect_pii("Las ventas en Colombia fueron de 1,000,000 COP")
        assert len(findings) == 0

    def test_empty_text(self):
        assert detect_pii("") == []
        assert detect_pii(None) == []


class TestSanitizeOutput:
    def test_sanitizes_email(self):
        text = "El cliente tiene email maria@gmail.com"
        sanitized, pii_found = sanitize_output(text)
        assert "[EMAIL_REDACTED]" in sanitized
        assert pii_found is True

    def test_no_sanitization_needed(self):
        text = "Revenue total: 5,000,000 COP"
        sanitized, pii_found = sanitize_output(text)
        assert sanitized == text
        assert pii_found is False

    def test_empty_text(self):
        sanitized, pii_found = sanitize_output("")
        assert sanitized == ""
        assert pii_found is False


class TestQuerySafety:
    def test_allows_select(self):
        safe, msg = validate_query_safety("SELECT * FROM gold_ventas_por_pais")
        assert safe is True

    def test_blocks_delete(self):
        safe, msg = validate_query_safety("DELETE FROM clientes")
        assert safe is False

    def test_blocks_drop(self):
        safe, msg = validate_query_safety("DROP TABLE clientes")
        assert safe is False

    def test_blocks_insert(self):
        safe, msg = validate_query_safety("INSERT INTO clientes VALUES (1)")
        assert safe is False

    def test_blocks_update(self):
        safe, msg = validate_query_safety("UPDATE clientes SET nombre='x'")
        assert safe is False
