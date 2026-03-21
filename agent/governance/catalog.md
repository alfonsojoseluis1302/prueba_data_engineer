# Catálogo de Datos — RetailTech S.A.S

## Tablas Fuente

### clientes
| Columna | Tipo | PII | Clasificación | Data Owner | Retención |
|---------|------|-----|---------------|------------|-----------|
| cliente_id | VARCHAR(10) | No | confidencial | crm@retailtech.co | 5 años |
| nombre | VARCHAR(100) | **Sí** | confidencial | crm@retailtech.co | 5 años |
| apellido | VARCHAR(100) | **Sí** | confidencial | crm@retailtech.co | 5 años |
| email | VARCHAR(200) | **Sí** | confidencial | crm@retailtech.co | 5 años |
| telefono | VARCHAR(30) | **Sí** | confidencial | crm@retailtech.co | 5 años |
| ciudad | VARCHAR(100) | No | interno | crm@retailtech.co | 1 año |
| pais | VARCHAR(50) | No | interno | crm@retailtech.co | 1 año |
| segmento | VARCHAR(20) | No | interno | marketing@retailtech.co | 1 año |
| fecha_registro | DATE | No | interno | crm@retailtech.co | 10 años |
| fecha_consentimiento | DATE | No | confidencial | legal@retailtech.co | 10 años |
| activo | BOOLEAN | No | interno | crm@retailtech.co | 1 año |

### productos
| Columna | Tipo | PII | Clasificación | Data Owner | Retención |
|---------|------|-----|---------------|------------|-----------|
| producto_id | VARCHAR(10) | No | interno | catalogo@retailtech.co | 10 años |
| nombre_producto | VARCHAR(200) | No | público | catalogo@retailtech.co | 10 años |
| categoria | VARCHAR(50) | No | público | catalogo@retailtech.co | 10 años |
| subcategoria | VARCHAR(50) | No | público | catalogo@retailtech.co | 10 años |
| precio_venta | DECIMAL(12,2) | No | interno | catalogo@retailtech.co | 1 año |
| costo | DECIMAL(12,2) | No | confidencial | finanzas@retailtech.co | 1 año |
| stock_disponible | INTEGER | No | interno | logistica@retailtech.co | 90 días |
| proveedor_id | VARCHAR(10) | No | interno | compras@retailtech.co | 5 años |
| nombre_proveedor | VARCHAR(200) | No | confidencial | compras@retailtech.co | 5 años |

### pedidos
| Columna | Tipo | PII | Clasificación | Data Owner | Retención |
|---------|------|-----|---------------|------------|-----------|
| pedido_id | VARCHAR(12) | No | interno | ventas@retailtech.co | 5 años |
| cliente_id | VARCHAR(10) | No | interno | ventas@retailtech.co | 5 años |
| fecha_pedido | DATE | No | interno | ventas@retailtech.co | 5 años |
| fecha_entrega | DATE | No | interno | logistica@retailtech.co | 5 años |
| estado | VARCHAR(20) | No | interno | ventas@retailtech.co | 1 año |
| canal | VARCHAR(20) | No | interno | ventas@retailtech.co | 5 años |
| metodo_pago | VARCHAR(30) | No | confidencial | finanzas@retailtech.co | 5 años |
| pais_envio | VARCHAR(50) | No | interno | logistica@retailtech.co | 5 años |
| total_bruto | DECIMAL(14,2) | No | confidencial | finanzas@retailtech.co | 5 años |
| total_neto | DECIMAL(14,2) | No | confidencial | finanzas@retailtech.co | 5 años |

### detalle_pedidos
| Columna | Tipo | PII | Clasificación | Data Owner | Retención |
|---------|------|-----|---------------|------------|-----------|
| item_id | VARCHAR(13) | No | interno | ventas@retailtech.co | 5 años |
| pedido_id | VARCHAR(12) | No | interno | ventas@retailtech.co | 5 años |
| producto_id | VARCHAR(10) | No | interno | ventas@retailtech.co | 5 años |
| cantidad | INTEGER | No | interno | ventas@retailtech.co | 5 años |
| precio_unitario | DECIMAL(12,2) | No | confidencial | ventas@retailtech.co | 5 años |
| subtotal | DECIMAL(14,2) | No | confidencial | ventas@retailtech.co | 5 años |

### eventos
| Columna | Tipo | PII | Clasificación | Data Owner | Retención |
|---------|------|-----|---------------|------------|-----------|
| evento_id | VARCHAR(12) | No | público | analytics@retailtech.co | 1 año |
| cliente_id | VARCHAR(10) | No | confidencial | analytics@retailtech.co | 1 año |
| session_id | VARCHAR(14) | No | interno | analytics@retailtech.co | 90 días |
| tipo_evento | VARCHAR(30) | No | público | analytics@retailtech.co | 1 año |
| timestamp | TIMESTAMP | No | interno | analytics@retailtech.co | 1 año |
| producto_id | VARCHAR(10) | No | público | analytics@retailtech.co | 1 año |
| dispositivo | VARCHAR(20) | No | público | analytics@retailtech.co | 1 año |
| pais | VARCHAR(50) | No | público | analytics@retailtech.co | 1 año |
| duracion_seg | INTEGER | No | público | analytics@retailtech.co | 90 días |

## Tablas Gold (Analíticas)

| Tabla | Descripción | Registros | Data Owner |
|-------|-------------|-----------|------------|
| gold_ventas_por_pais | Revenue agregado por país | 6 | ventas@retailtech.co |
| gold_ventas_por_canal | Revenue por canal de venta | 4 | ventas@retailtech.co |
| gold_ventas_mensuales | Serie temporal de ventas | 24 | ventas@retailtech.co |
| gold_top_productos | Ranking de productos por ingreso | 80 | catalogo@retailtech.co |
| gold_segmento_clientes | Métricas por segmento | 4 | marketing@retailtech.co |
| gold_conversion_funnel | Funnel de conversión digital | 4 | analytics@retailtech.co |
| gold_clientes_rfm | Segmentación RFM | 261 | crm@retailtech.co |
| gold_resumen_calidad | Métricas de calidad de datos | 5 | governance@retailtech.co |
