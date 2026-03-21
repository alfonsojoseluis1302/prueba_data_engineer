"""Enmascaramiento PII para capa Silver."""

import hashlib
import re
import pandas as pd

# Patrones PII para detección
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"\b\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b|\b57\d{10}\b|\b\d{10,12}\b")
NAME_PATTERN = re.compile(
    r"\b(?:nombre|apellido|name)\b", re.IGNORECASE
)

# Lista blanca de términos seguros (no son PII aunque coincidan con patrones)
SAFE_TERMS = {
    "colombia", "méxico", "mexico", "argentina", "chile", "perú", "peru", "ecuador",
    "bogotá", "bogota", "medellín", "medellin", "cali", "lima", "santiago",
    "buenos aires", "quito", "guayaquil", "ciudad de méxico",
    "b2b", "b2c", "marketplace",
    "electrónica", "electronica", "hogar", "ropa", "deportes", "libros",
    "unknown@retailtech.co",
}


def sha256_hash(value: str) -> str:
    """Genera hash SHA-256 de un valor."""
    if pd.isna(value) or str(value).strip() == "":
        return value
    return hashlib.sha256(str(value).encode()).hexdigest()


def mask_email(email: str) -> str:
    """Enmascara email con SHA-256."""
    if pd.isna(email) or email == "unknown@retailtech.co":
        return email
    return sha256_hash(email)


def mask_name(name: str) -> str:
    """Enmascara nombre/apellido con SHA-256."""
    if pd.isna(name):
        return name
    return sha256_hash(name)


def mask_phone(phone: str) -> str:
    """Enmascara teléfono mostrando solo últimos 4 dígitos."""
    if pd.isna(phone):
        return phone
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) < 4:
        return "****"
    return "****" + digits[-4:]


def mask_clientes_pii(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica masking PII a la tabla clientes."""
    df = df.copy()
    df["email"] = df["email"].apply(mask_email)
    df["nombre"] = df["nombre"].apply(mask_name)
    df["apellido"] = df["apellido"].apply(mask_name)
    df["telefono"] = df["telefono"].apply(mask_phone)
    # fecha_consentimiento se conserva (es metadata legal, no PII directa)
    return df


def detect_pii_in_text(text: str) -> list[dict]:
    """Detecta posible PII en un texto libre. Retorna lista de hallazgos."""
    if not text or not isinstance(text, str):
        return []

    findings = []
    text_lower = text.lower()

    # Emails
    for match in EMAIL_PATTERN.finditer(text):
        email = match.group().lower()
        if email not in SAFE_TERMS:
            findings.append({"type": "email", "value": match.group(), "position": match.start()})

    # Teléfonos
    for match in PHONE_PATTERN.finditer(text):
        findings.append({"type": "phone", "value": match.group(), "position": match.start()})

    return findings


def sanitize_text(text: str) -> str:
    """Remueve PII detectada de un texto."""
    if not text:
        return text

    # Reemplazar emails
    text = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
    # Reemplazar teléfonos
    text = PHONE_PATTERN.sub("[PHONE_REDACTED]", text)

    return text
