"""Guardrails: detección y filtrado de PII en outputs del agente."""

import re

# Patrones PII
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\b\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b|\b57\d{10}\b|\b\d{10,12}\b")
# Patrón para detectar hashes SHA-256 parciales (los que se usan como masking)
SHA_PARTIAL_RE = re.compile(r"\b[a-f0-9]{64}\b")

# Whitelist de términos seguros
SAFE_TERMS = {
    # Emails corporativos (no son PII de usuarios)
    "unknown@retailtech.co", "crm@retailtech.co", "marketing@retailtech.co",
    "ventas@retailtech.co", "catalogo@retailtech.co", "analytics@retailtech.co",
    "governance@retailtech.co", "finanzas@retailtech.co", "logistica@retailtech.co",
    "compras@retailtech.co", "legal@retailtech.co",
    # Países
    "colombia", "méxico", "mexico", "argentina", "chile", "perú", "peru", "ecuador",
    # Ciudades comunes
    "bogotá", "bogota", "medellín", "medellin", "cali", "barranquilla",
    "lima", "santiago", "buenos aires", "quito", "guayaquil",
    # Categorías
    "electrónica", "electronica", "hogar", "ropa", "deportes", "libros",
    # Segmentos
    "b2b", "b2c", "marketplace", "enterprise",
}


def detect_pii(text: str) -> list[dict]:
    """Detecta posible PII en texto."""
    if not text:
        return []

    findings = []
    text_lower = text.lower()

    # Emails
    for match in EMAIL_RE.finditer(text):
        email = match.group().lower()
        if email not in SAFE_TERMS:
            findings.append({"type": "email", "value": match.group()})

    # Teléfonos (excluir contexto numérico de queries/resultados)
    for match in PHONE_RE.finditer(text):
        value = match.group()
        # Si está rodeado de contexto numérico de tabla, podría ser un ID o monto
        if not re.search(r"(telefono|phone|cel|móvil)", text_lower):
            continue
        findings.append({"type": "phone", "value": value})

    return findings


def sanitize_output(text: str) -> tuple[str, bool]:
    """Sanitiza el output del agente removiendo PII.

    Retorna: (texto_sanitizado, pii_encontrada)
    """
    if not text:
        return text, False

    findings = detect_pii(text)
    if not findings:
        return text, False

    sanitized = text
    for finding in findings:
        if finding["type"] == "email":
            sanitized = sanitized.replace(finding["value"], "[EMAIL_REDACTED]")
        elif finding["type"] == "phone":
            sanitized = sanitized.replace(finding["value"], "[PHONE_REDACTED]")

    return sanitized, True


def validate_query_safety(query: str) -> tuple[bool, str]:
    """Valida que una query SQL sea segura para ejecutar.

    Retorna: (es_segura, mensaje)
    """
    query_upper = query.upper().strip()

    # Solo SELECT
    if not query_upper.startswith("SELECT"):
        return False, "Solo se permiten consultas SELECT."

    # Bloquear DDL/DML
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    for keyword in dangerous:
        if re.search(rf"\b{keyword}\b", query_upper):
            return False, f"Operación '{keyword}' no permitida."

    return True, "OK"
