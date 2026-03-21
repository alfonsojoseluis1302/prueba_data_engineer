# Linaje de Datos — RetailTech S.A.S

## Flujo General

```
DataSource/ (CSVs generados)
    │
    ▼ Copia inmutable
pipeline/data/raw/
    │
    ▼ Bronze: metadatos + hash + timestamp
pipeline/data/bronze/ (Parquet)
    │
    ▼ Silver: limpieza + PII masking
pipeline/data/silver/ (Parquet)
    │
    ▼ Gold: agregaciones
pipeline/data/gold/ (Parquet + DuckDB)
```

## Linaje por Tabla

### clientes
```
raw/clientes.csv
  → bronze/clientes.parquet   [+_source_file, +_ingestion_timestamp, +_row_hash, tipado fechas]
  → silver/clientes.parquet   [fix emails null→placeholder, fix telefono N/A→null,
                                fix ciudad vacía→Desconocida, PII masking SHA-256]
  → gold_segmento_clientes    [GROUP BY segmento → métricas agregadas]
  → gold_clientes_rfm         [RFM scoring por cliente_id (masked)]
```

### productos
```
raw/productos.csv
  → bronze/productos.parquet  [+metadatos, tipado fechas]
  → silver/productos.parquet  [fix stock null→0]
  → gold_top_productos        [JOIN con detalle_pedidos, GROUP BY producto]
```

### pedidos
```
raw/pedidos.csv
  → bronze/pedidos.parquet    [+metadatos, tipado fechas]
  → silver/pedidos.parquet    [deduplicación por pedido_id keep first]
  → gold_ventas_por_pais      [GROUP BY pais_envio]
  → gold_ventas_por_canal     [GROUP BY canal]
  → gold_ventas_mensuales     [GROUP BY mes]
  → gold_segmento_clientes    [JOIN clientes, GROUP BY segmento]
  → gold_clientes_rfm         [GROUP BY cliente_id → R, F, M]
```

### detalle_pedidos
```
raw/detalle_pedidos.csv
  → bronze/detalle_pedidos.parquet  [+metadatos]
  → silver/detalle_pedidos.parquet  [sin cambios]
  → gold_top_productos              [JOIN productos, GROUP BY producto]
```

### eventos
```
raw/eventos.csv
  → bronze/eventos.parquet    [+metadatos, tipado timestamp]
  → silver/eventos.parquet    [fix duracion_seg null→mediana por tipo_evento]
  → gold_conversion_funnel    [GROUP BY tipo_evento, funnel ordering]
```

## Transformaciones Aplicadas

| Capa | Tabla | Transformación | Campo |
|------|-------|----------------|-------|
| Bronze | todas | Agregar _source_file | metadata |
| Bronze | todas | Agregar _ingestion_timestamp | metadata |
| Bronze | todas | Agregar _row_hash (SHA-256) | metadata |
| Bronze | todas | Parsear columnas de fecha | tipado |
| Silver | clientes | null → "unknown@retailtech.co" | email |
| Silver | clientes | "N/A" → null | telefono |
| Silver | clientes | vacío → "Desconocida" | ciudad |
| Silver | clientes | SHA-256 masking | email, nombre, apellido |
| Silver | clientes | Últimos 4 dígitos | telefono |
| Silver | productos | null → 0 | stock_disponible |
| Silver | pedidos | Deduplicación (keep first) | pedido_id |
| Silver | eventos | null → mediana por tipo_evento | duracion_seg |
| Gold | múltiples | Agregaciones GROUP BY | tablas analíticas |
| Gold | gold_clientes_rfm | Scoring RFM 1-5 | recency, frequency, monetary |
