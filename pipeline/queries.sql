-- Queries de negocio para RetailTech S.A.S
-- Ejecutar después de la capa Gold (tablas cargadas en DuckDB)

-- @name: q01_top_productos_ingreso
-- Top 10 productos por ingreso total
SELECT
    producto_id,
    nombre_producto,
    categoria,
    unidades_vendidas,
    ROUND(revenue, 2) AS revenue
FROM gold_top_productos
ORDER BY revenue DESC
LIMIT 10;

-- @name: q02_ventas_por_pais
-- Ventas totales por país
SELECT
    pais_envio AS pais,
    total_pedidos,
    ROUND(revenue_neto, 2) AS revenue_neto,
    ROUND(ticket_promedio, 2) AS ticket_promedio
FROM gold_ventas_por_pais
ORDER BY revenue_neto DESC;

-- @name: q03_conversion_por_canal
-- Tasa de conversión por canal de venta
SELECT
    canal,
    total_pedidos,
    ROUND(revenue_neto, 2) AS revenue_neto,
    ROUND(revenue_neto / total_pedidos, 2) AS revenue_por_pedido
FROM gold_ventas_por_canal
ORDER BY revenue_neto DESC;

-- @name: q04_clientes_b2b_grandes
-- Clientes B2B con compras superiores a 500,000 COP
SELECT
    p.cliente_id,
    c.segmento,
    COUNT(p.pedido_id) AS total_pedidos,
    ROUND(SUM(p.total_neto), 2) AS total_compras
FROM pedidos p
JOIN clientes c ON p.cliente_id = c.cliente_id
WHERE c.segmento = 'B2B'
GROUP BY p.cliente_id, c.segmento
HAVING SUM(p.total_neto) > 500000
ORDER BY total_compras DESC;

-- @name: q05_colombia_vs_mexico
-- Comparativa Colombia vs México
SELECT
    pais_envio AS pais,
    COUNT(*) AS total_pedidos,
    ROUND(SUM(total_neto), 2) AS revenue_neto,
    ROUND(AVG(total_neto), 2) AS ticket_promedio,
    ROUND(AVG(descuento_pct) * 100, 2) AS descuento_prom_pct
FROM pedidos
WHERE pais_envio IN ('Colombia', 'México')
GROUP BY pais_envio;

-- @name: q06_top5_productos_h2_2024
-- Top 5 productos del segundo semestre 2024
SELECT
    dp.producto_id,
    pr.nombre_producto,
    pr.categoria,
    SUM(dp.cantidad) AS unidades,
    ROUND(SUM(dp.subtotal), 2) AS revenue
FROM detalle_pedidos dp
JOIN pedidos p ON dp.pedido_id = p.pedido_id
JOIN productos pr ON dp.producto_id = pr.producto_id
WHERE p.fecha_pedido >= '2024-07-01' AND p.fecha_pedido <= '2024-12-31'
GROUP BY dp.producto_id, pr.nombre_producto, pr.categoria
ORDER BY revenue DESC
LIMIT 5;

-- @name: q07_metodo_pago_por_pais
-- Método de pago preferido por país
SELECT
    pais_envio AS pais,
    metodo_pago,
    COUNT(*) AS total_pedidos,
    ROUND(SUM(total_neto), 2) AS revenue_neto
FROM pedidos
GROUP BY pais_envio, metodo_pago
ORDER BY pais, total_pedidos DESC;

-- @name: q08_tasa_cancelacion_devolucion
-- Tasa de cancelación y devolución
SELECT
    estado,
    COUNT(*) AS total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM pedidos), 2) AS porcentaje
FROM pedidos
WHERE estado IN ('cancelado', 'devuelto')
GROUP BY estado;

-- @name: q09_margen_bruto_categoria
-- Margen bruto por categoría de producto
SELECT
    pr.categoria,
    ROUND(AVG((pr.precio_venta - pr.costo) / pr.precio_venta * 100), 2) AS margen_bruto_pct,
    ROUND(SUM(dp.subtotal), 2) AS revenue_total,
    SUM(dp.cantidad) AS unidades_vendidas
FROM detalle_pedidos dp
JOIN productos pr ON dp.producto_id = pr.producto_id
GROUP BY pr.categoria
ORDER BY revenue_total DESC;

-- @name: q10_actividad_horaria
-- Actividad horaria de eventos digitales
SELECT
    EXTRACT(HOUR FROM timestamp) AS hora,
    tipo_evento,
    COUNT(*) AS total_eventos
FROM eventos
GROUP BY hora, tipo_evento
ORDER BY hora, total_eventos DESC;

-- @name: q11_segmentacion_rfm
-- Distribución de segmentación RFM
SELECT
    rfm_score,
    COUNT(*) AS total_clientes,
    ROUND(AVG(recency), 1) AS recency_promedio,
    ROUND(AVG(frequency), 1) AS frequency_promedio,
    ROUND(AVG(monetary), 2) AS monetary_promedio
FROM gold_clientes_rfm
GROUP BY rfm_score
ORDER BY total_clientes DESC
LIMIT 20;

-- @name: q12_cohorte_retencion_mensual
-- Cohorte mensual de retención: primer mes de compra vs meses siguientes
WITH first_purchase AS (
    SELECT
        cliente_id,
        DATE_TRUNC('month', MIN(fecha_pedido)) AS cohorte
    FROM pedidos
    GROUP BY cliente_id
),
monthly_activity AS (
    SELECT
        p.cliente_id,
        DATE_TRUNC('month', p.fecha_pedido) AS mes_actividad
    FROM pedidos p
    GROUP BY p.cliente_id, DATE_TRUNC('month', p.fecha_pedido)
)
SELECT
    fp.cohorte,
    DATEDIFF('month', fp.cohorte, ma.mes_actividad) AS meses_desde_cohorte,
    COUNT(DISTINCT ma.cliente_id) AS clientes_activos
FROM first_purchase fp
JOIN monthly_activity ma ON fp.cliente_id = ma.cliente_id
WHERE DATEDIFF('month', fp.cohorte, ma.mes_actividad) >= 0
GROUP BY fp.cohorte, meses_desde_cohorte
ORDER BY fp.cohorte, meses_desde_cohorte;
