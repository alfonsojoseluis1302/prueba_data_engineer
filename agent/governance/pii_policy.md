# Política de Protección de Datos Personales (PII)

## Marco Legal
- **Colombia:** Ley 1581 de 2012 (Protección de Datos Personales)
- **Referencia internacional:** GDPR (Reglamento General de Protección de Datos)

## Campos PII Identificados

| Tabla | Campo | Tipo PII | Método de Masking | Capa |
|-------|-------|----------|-------------------|------|
| clientes | nombre | Nombre personal | SHA-256 hash | Silver |
| clientes | apellido | Nombre personal | SHA-256 hash | Silver |
| clientes | email | Email personal | SHA-256 hash | Silver |
| clientes | telefono | Teléfono personal | Últimos 4 dígitos | Silver |
| clientes | fecha_consentimiento | Metadata legal | Sin masking (fecha) | — |

## Medidas Implementadas

### 1. Masking en Pipeline (Silver)
- **SHA-256** para nombre, apellido, email: transformación irreversible que permite joins por ID pero impide reconstruir datos originales.
- **Últimos 4 dígitos** para teléfono: suficiente para verificación parcial sin exponer el número completo.
- El masking se aplica **antes** de cualquier agregación (Gold).

### 2. Guardrails del Agente
- **Detección regex** de patrones PII (email, teléfono) en outputs del LLM.
- **Sanitización automática**: PII detectada se reemplaza con `[EMAIL_REDACTED]`, `[PHONE_REDACTED]`.
- **Whitelist** de términos seguros (emails corporativos, ciudades, países, categorías).
- **Filtrado de columnas**: la herramienta `ejecutar_sql` elimina automáticamente columnas PII del resultado.

### 3. Validación SQL
- Solo se permiten queries `SELECT` (no INSERT, UPDATE, DELETE, DROP).
- El agente opera sobre tablas Gold (datos agregados) preferentemente.
- Las tablas Silver tienen PII enmascarada.

### 4. Datos Raw
- Los datos raw (`pipeline/data/raw/`) contienen PII original.
- Están en `.gitignore` para los datos procesados (bronze/silver/gold).
- El acceso a raw debe ser restringido en un entorno productivo.

## Clasificación de Datos

| Nivel | Descripción | Ejemplos |
|-------|-------------|----------|
| **Confidencial** | PII, datos financieros | nombre, email, costos, métodos de pago |
| **Interno** | Datos operativos | pedidos, stock, segmentos |
| **Público** | Datos de catálogo | nombres de productos, categorías, eventos |

## Retención

- PII de clientes: 5 años (Ley 1581)
- Datos operativos: 1-5 años según tipo
- Eventos digitales: 90 días - 1 año
- Consentimiento: 10 años (auditoría legal)
