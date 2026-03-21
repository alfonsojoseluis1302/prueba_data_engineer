# Control de Acceso del Agente

## Principio de Mínimo Privilegio
El agente conversacional tiene acceso **de solo lectura** a un subconjunto controlado de datos.

## Acceso Permitido

### Tablas Gold (preferidas)
| Tabla | Acceso | Datos sensibles |
|-------|--------|-----------------|
| gold_ventas_por_pais | ✅ Lectura | No |
| gold_ventas_por_canal | ✅ Lectura | No |
| gold_ventas_mensuales | ✅ Lectura | No |
| gold_top_productos | ✅ Lectura | No |
| gold_segmento_clientes | ✅ Lectura | No |
| gold_conversion_funnel | ✅ Lectura | No |
| gold_clientes_rfm | ✅ Lectura | IDs masked |
| gold_resumen_calidad | ✅ Lectura | No |

### Tablas Silver (con PII masked)
| Tabla | Acceso | Nota |
|-------|--------|------|
| clientes | ✅ Lectura | PII enmascarada (SHA-256) |
| productos | ✅ Lectura | Sin PII |
| pedidos | ✅ Lectura | Sin PII directa |
| detalle_pedidos | ✅ Lectura | Sin PII |
| eventos | ✅ Lectura | cliente_id nullable |

## Acceso Denegado

| Recurso | Motivo |
|---------|--------|
| Datos raw | Contienen PII sin masking |
| Operaciones DDL (CREATE, DROP, ALTER) | Solo lectura |
| Operaciones DML (INSERT, UPDATE, DELETE) | Solo lectura |
| Sistema de archivos | El agente no tiene acceso a archivos fuera de reportes |

## Controles de Seguridad

1. **Validación SQL**: solo queries `SELECT` son ejecutadas
2. **Filtrado de columnas PII**: automático en resultados de queries
3. **Sanitización de output**: regex para detectar PII residual en respuestas del LLM
4. **Límite de resultados**: máximo 50 filas por query para evitar data exfiltration
5. **Timeout de sesión**: sesiones expiran tras 60 minutos de inactividad
6. **Historial limitado**: máximo 20 mensajes por sesión

## Herramientas del Agente

| Herramienta | Función | Restricciones |
|-------------|---------|---------------|
| `ejecutar_sql` | Ejecutar queries SELECT | Solo SELECT, filtro PII, límite 50 filas |
| `obtener_esquema` | Ver estructura de tablas | Solo tablas permitidas |
| `resumir_reporte_calidad` | Ver reportes de calidad | Solo lectura, contenido truncado |
