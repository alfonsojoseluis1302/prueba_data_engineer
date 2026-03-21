"""
=============================================================
  GENERADOR DE DATASET - PRUEBA TÉCNICA DATA ENGINEER
  Empresa: RetailTech S.A.S  |  Dominio: E-Commerce
  Herramienta de soporte para candidatos
=============================================================
Ejecutar: python generar_dataset.py
Requiere: pip install pandas faker numpy
=============================================================
!pip install Faker
"""

import os
import random
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

fake = Faker("es_CO")
random.seed(42)
np.random.seed(42)

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# PARÁMETROS
# ─────────────────────────────────────────────
N_CLIENTES   = 300
N_PRODUCTOS  = 80
N_PEDIDOS    = 1_200
N_EVENTOS    = 4_000

START_DATE   = datetime(2023, 1, 1)
END_DATE     = datetime(2024, 12, 31)

SEGMENTOS    = ["B2C", "B2B", "Premium", "Inactivo"]
CANALES      = ["web", "mobile", "tienda_fisica", "marketplace"]
METODOS_PAGO = ["tarjeta_credito", "PSE", "efectivo", "transferencia", "credito_tienda"]
ESTADOS_PED  = ["pendiente", "enviado", "entregado", "cancelado", "devuelto"]
CATEGORIAS   = {
    "Electrónica":    ["Smartphones", "Laptops", "Tabletas", "Accesorios"],
    "Hogar":          ["Cocina", "Dormitorio", "Decoración", "Limpieza"],
    "Ropa":           ["Hombre", "Mujer", "Niños", "Deportiva"],
    "Deportes":       ["Fitness", "Outdoor", "Ciclismo", "Natación"],
    "Alimentos":      ["Snacks", "Bebidas", "Orgánicos", "Importados"],
}
TIPOS_EVENTO = ["page_view", "search", "add_to_cart", "checkout", "purchase", "remove_from_cart"]
CLASIFICACION_DATO = ["público", "interno", "confidencial", "restringido"]
PAISES = ["Colombia", "México", "Chile", "Perú", "Argentina", "Ecuador"]


def rand_date(start=START_DATE, end=END_DATE):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


# ─────────────────────────────────────────────
# 1. CLIENTES
# ─────────────────────────────────────────────
print("Generando clientes...")
clientes = []
for i in range(1, N_CLIENTES + 1):
    reg_date  = rand_date()
    consent_d = reg_date + timedelta(days=random.randint(0, 5))
    segmento  = random.choices(SEGMENTOS, weights=[50, 20, 20, 10])[0]
    pais      = random.choices(PAISES, weights=[60, 15, 8, 7, 6, 4])[0]

    # Introducir intencionalmente algunos problemas de calidad
    email = fake.email() if random.random() > 0.05 else None            # 5% nulos
    phone = fake.phone_number() if random.random() > 0.08 else "N/A"   # 8% inválidos
    ciudad = fake.city() if random.random() > 0.03 else ""

    clientes.append({
        "cliente_id":          f"CLI-{i:05d}",
        "nombre":              fake.first_name(),
        "apellido":            fake.last_name(),
        "email":               email,
        "telefono":            phone,
        "ciudad":              ciudad,
        "pais":                pais,
        "segmento":            segmento,
        "fecha_registro":      reg_date.strftime("%Y-%m-%d"),
        "fecha_consentimiento":consent_d.strftime("%Y-%m-%d"),
        "activo":              random.choices([True, False], weights=[85, 15])[0],
        "data_owner":          random.choice(["marketing@retailtech.co", "crm@retailtech.co"]),
        "clasificacion_dato":  "confidencial",   # PII
    })

df_clientes = pd.DataFrame(clientes)
df_clientes.to_csv(f"{OUTPUT_DIR}/clientes.csv", index=False)
print(f"  ✓ {len(df_clientes)} clientes generados")


# ─────────────────────────────────────────────
# 2. PRODUCTOS
# ─────────────────────────────────────────────
print("Generando productos...")
productos = []
proveedores = [f"PROV-{j:03d}" for j in range(1, 16)]

for i in range(1, N_PRODUCTOS + 1):
    categoria = random.choice(list(CATEGORIAS.keys()))
    subcat     = random.choice(CATEGORIAS[categoria])
    costo      = round(random.uniform(10_000, 800_000), 2)
    precio     = round(costo * random.uniform(1.2, 2.5), 2)
    stock      = random.randint(0, 500) if random.random() > 0.05 else None  # 5% nulos

    productos.append({
        "producto_id":         f"PROD-{i:04d}",
        "nombre_producto":     f"{subcat} {fake.word().capitalize()} {random.randint(100,999)}",
        "categoria":           categoria,
        "subcategoria":        subcat,
        "precio_venta":        precio,
        "costo":               costo,
        "stock_disponible":    stock,
        "proveedor_id":        random.choice(proveedores),
        "nombre_proveedor":    fake.company(),
        "fecha_creacion":      rand_date(START_DATE, datetime(2023, 6, 30)).strftime("%Y-%m-%d"),
        "activo":              random.choices([True, False], weights=[90, 10])[0],
        "data_owner":          "catalogo@retailtech.co",
        "clasificacion_dato":  "interno",
    })

df_productos = pd.DataFrame(productos)
df_productos.to_csv(f"{OUTPUT_DIR}/productos.csv", index=False)
print(f"  ✓ {len(df_productos)} productos generados")


# ─────────────────────────────────────────────
# 3. PEDIDOS
# ─────────────────────────────────────────────
print("Generando pedidos...")
pedidos = []
cliente_ids  = df_clientes["cliente_id"].tolist()
activos_ids  = df_clientes[df_clientes["activo"] == True]["cliente_id"].tolist()

for i in range(1, N_PEDIDOS + 1):
    estado       = random.choices(ESTADOS_PED, weights=[5, 15, 60, 12, 8])[0]
    orden_date   = rand_date()
    entrega_date = None
    if estado in ("entregado", "devuelto"):
        entrega_date = (orden_date + timedelta(days=random.randint(1, 15))).strftime("%Y-%m-%d")

    descuento = round(random.uniform(0, 0.3), 2) if random.random() > 0.6 else 0.0
    total     = round(random.uniform(25_000, 3_500_000), 2)

    # Introducir duplicado intencional (~2%)
    dup_id = f"PED-{i:06d}" if random.random() > 0.02 else f"PED-{random.randint(1, i):06d}"

    pedidos.append({
        "pedido_id":        dup_id,
        "cliente_id":       random.choice(activos_ids),
        "fecha_pedido":     orden_date.strftime("%Y-%m-%d"),
        "fecha_entrega":    entrega_date,
        "estado":           estado,
        "canal":            random.choice(CANALES),
        "metodo_pago":      random.choice(METODOS_PAGO),
        "pais_envio":       random.choice(PAISES),
        "total_bruto":      total,
        "descuento_pct":    descuento,
        "total_neto":       round(total * (1 - descuento), 2),
        "data_owner":       "ventas@retailtech.co",
        "clasificacion_dato": "interno",
    })

df_pedidos = pd.DataFrame(pedidos)
df_pedidos.to_csv(f"{OUTPUT_DIR}/pedidos.csv", index=False)
print(f"  ✓ {len(df_pedidos)} pedidos generados")


# ─────────────────────────────────────────────
# 4. DETALLE DE PEDIDOS
# ─────────────────────────────────────────────
print("Generando detalle de pedidos...")
detalles = []
producto_ids = df_productos["producto_id"].tolist()
item_id = 1

for _, row in df_pedidos.iterrows():
    n_items = random.randint(1, 6)
    prods   = random.sample(producto_ids, min(n_items, len(producto_ids)))
    for pid in prods:
        prod_row    = df_productos[df_productos["producto_id"] == pid].iloc[0]
        cantidad    = random.randint(1, 5)
        precio_unit = prod_row["precio_venta"]
        desc_pct    = round(random.uniform(0, 0.2), 2) if random.random() > 0.7 else 0.0

        detalles.append({
            "item_id":        f"ITEM-{item_id:07d}",
            "pedido_id":      row["pedido_id"],
            "producto_id":    pid,
            "cantidad":       cantidad,
            "precio_unitario":precio_unit,
            "descuento_pct":  desc_pct,
            "subtotal":       round(cantidad * precio_unit * (1 - desc_pct), 2),
            "data_owner":     "ventas@retailtech.co",
            "clasificacion_dato": "interno",
        })
        item_id += 1

df_detalles = pd.DataFrame(detalles)
df_detalles.to_csv(f"{OUTPUT_DIR}/detalle_pedidos.csv", index=False)
print(f"  ✓ {len(df_detalles)} ítems de pedido generados")


# ─────────────────────────────────────────────
# 5. EVENTOS DIGITALES
# ─────────────────────────────────────────────
print("Generando eventos digitales...")
eventos = []
session_pool = [f"SES-{k:08d}" for k in range(1, 2001)]

for i in range(1, N_EVENTOS + 1):
    evt_date  = rand_date()
    evt_hour  = random.randint(0, 23)
    evt_min   = random.randint(0, 59)
    evt_sec   = random.randint(0, 59)
    timestamp = datetime(evt_date.year, evt_date.month, evt_date.day,
                         evt_hour, evt_min, evt_sec)

    cliente = random.choice(cliente_ids) if random.random() > 0.3 else None  # 30% anónimos
    tipo    = random.choices(TIPOS_EVENTO, weights=[30, 20, 20, 10, 10, 10])[0]
    prod    = random.choice(producto_ids) if tipo in ("add_to_cart", "purchase", "remove_from_cart") else None

    eventos.append({
        "evento_id":       f"EVT-{i:07d}",
        "cliente_id":      cliente,
        "session_id":      random.choice(session_pool),
        "tipo_evento":     tipo,
        "timestamp":       timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "producto_id":     prod,
        "dispositivo":     random.choice(["desktop", "mobile", "tablet"]),
        "pais":            random.choices(PAISES, weights=[60, 15, 8, 7, 6, 4])[0],
        "duracion_seg":    random.randint(1, 600) if random.random() > 0.05 else None,
        "data_owner":      "analytics@retailtech.co",
        "clasificacion_dato": "público",
    })

df_eventos = pd.DataFrame(eventos)
df_eventos.to_csv(f"{OUTPUT_DIR}/eventos.csv", index=False)
print(f"  ✓ {len(df_eventos)} eventos generados")


# ─────────────────────────────────────────────
# 6. DICCIONARIO DE DATOS (Activo de Gobernanza)
# ─────────────────────────────────────────────
print("Generando diccionario de datos...")

diccionario = [
    # CLIENTES
    ("clientes","cliente_id","VARCHAR(10)","Identificador único del cliente","No","crm@retailtech.co",1825,"confidencial","PK"),
    ("clientes","nombre","VARCHAR(100)","Nombre de pila del cliente","Sí","crm@retailtech.co",1825,"confidencial",""),
    ("clientes","apellido","VARCHAR(100)","Apellido del cliente","Sí","crm@retailtech.co",1825,"confidencial",""),
    ("clientes","email","VARCHAR(200)","Correo electrónico de contacto","Sí","crm@retailtech.co",1825,"confidencial",""),
    ("clientes","telefono","VARCHAR(30)","Teléfono de contacto","Sí","crm@retailtech.co",1825,"confidencial",""),
    ("clientes","ciudad","VARCHAR(100)","Ciudad de residencia","No","crm@retailtech.co",365,"interno",""),
    ("clientes","pais","VARCHAR(50)","País de residencia","No","crm@retailtech.co",365,"interno",""),
    ("clientes","segmento","VARCHAR(20)","Segmento comercial del cliente","No","marketing@retailtech.co",365,"interno",""),
    ("clientes","fecha_registro","DATE","Fecha en que el cliente se registró","No","crm@retailtech.co",3650,"interno",""),
    ("clientes","fecha_consentimiento","DATE","Fecha de aceptación de política de datos (GDPR/Ley 1581)","No","legal@retailtech.co",3650,"confidencial",""),
    ("clientes","activo","BOOLEAN","Indica si el cliente está activo","No","crm@retailtech.co",365,"interno",""),
    ("clientes","data_owner","VARCHAR(100)","Correo del responsable del dato","No","governance@retailtech.co",3650,"interno",""),
    ("clientes","clasificacion_dato","VARCHAR(20)","Nivel de clasificación de seguridad","No","governance@retailtech.co",3650,"interno",""),
    # PRODUCTOS
    ("productos","producto_id","VARCHAR(10)","Identificador único del producto","No","catalogo@retailtech.co",3650,"interno","PK"),
    ("productos","nombre_producto","VARCHAR(200)","Nombre comercial del producto","No","catalogo@retailtech.co",3650,"público",""),
    ("productos","categoria","VARCHAR(50)","Categoría principal del producto","No","catalogo@retailtech.co",3650,"público",""),
    ("productos","subcategoria","VARCHAR(50)","Subcategoría del producto","No","catalogo@retailtech.co",3650,"público",""),
    ("productos","precio_venta","DECIMAL(12,2)","Precio de venta al público (COP)","No","catalogo@retailtech.co",365,"interno",""),
    ("productos","costo","DECIMAL(12,2)","Costo de adquisición (COP)","No","finanzas@retailtech.co",365,"confidencial",""),
    ("productos","stock_disponible","INTEGER","Unidades disponibles en inventario","No","logistica@retailtech.co",90,"interno",""),
    ("productos","proveedor_id","VARCHAR(10)","ID del proveedor","No","compras@retailtech.co",1825,"interno","FK"),
    ("productos","nombre_proveedor","VARCHAR(200)","Nombre del proveedor","No","compras@retailtech.co",1825,"confidencial",""),
    ("productos","fecha_creacion","DATE","Fecha de alta del producto","No","catalogo@retailtech.co",3650,"interno",""),
    ("productos","activo","BOOLEAN","Indica si el producto está disponible","No","catalogo@retailtech.co",365,"interno",""),
    # PEDIDOS
    ("pedidos","pedido_id","VARCHAR(12)","Identificador único del pedido","No","ventas@retailtech.co",1825,"interno","PK"),
    ("pedidos","cliente_id","VARCHAR(10)","FK al cliente que realizó el pedido","No","ventas@retailtech.co",1825,"interno","FK"),
    ("pedidos","fecha_pedido","DATE","Fecha en que se realizó el pedido","No","ventas@retailtech.co",1825,"interno",""),
    ("pedidos","fecha_entrega","DATE","Fecha de entrega efectiva (NULL si no entregado)","No","logistica@retailtech.co",1825,"interno",""),
    ("pedidos","estado","VARCHAR(20)","Estado actual del pedido","No","ventas@retailtech.co",365,"interno",""),
    ("pedidos","canal","VARCHAR(20)","Canal de venta","No","ventas@retailtech.co",1825,"interno",""),
    ("pedidos","metodo_pago","VARCHAR(30)","Método de pago utilizado","No","finanzas@retailtech.co",1825,"confidencial",""),
    ("pedidos","pais_envio","VARCHAR(50)","País destino del envío","No","logistica@retailtech.co",1825,"interno",""),
    ("pedidos","total_bruto","DECIMAL(14,2)","Total del pedido antes de descuentos (COP)","No","finanzas@retailtech.co",1825,"confidencial",""),
    ("pedidos","descuento_pct","DECIMAL(5,2)","Porcentaje de descuento aplicado","No","ventas@retailtech.co",1825,"interno",""),
    ("pedidos","total_neto","DECIMAL(14,2)","Total final pagado (COP)","No","finanzas@retailtech.co",1825,"confidencial",""),
    # DETALLE PEDIDOS
    ("detalle_pedidos","item_id","VARCHAR(13)","Identificador único de línea de pedido","No","ventas@retailtech.co",1825,"interno","PK"),
    ("detalle_pedidos","pedido_id","VARCHAR(12)","FK al pedido","No","ventas@retailtech.co",1825,"interno","FK"),
    ("detalle_pedidos","producto_id","VARCHAR(10)","FK al producto","No","ventas@retailtech.co",1825,"interno","FK"),
    ("detalle_pedidos","cantidad","INTEGER","Unidades pedidas","No","ventas@retailtech.co",1825,"interno",""),
    ("detalle_pedidos","precio_unitario","DECIMAL(12,2)","Precio unitario al momento de la compra (COP)","No","ventas@retailtech.co",1825,"confidencial",""),
    ("detalle_pedidos","descuento_pct","DECIMAL(5,2)","Descuento por ítem","No","ventas@retailtech.co",1825,"interno",""),
    ("detalle_pedidos","subtotal","DECIMAL(14,2)","Subtotal de la línea (COP)","No","ventas@retailtech.co",1825,"confidencial",""),
    # EVENTOS
    ("eventos","evento_id","VARCHAR(12)","Identificador único del evento digital","No","analytics@retailtech.co",365,"público","PK"),
    ("eventos","cliente_id","VARCHAR(10)","FK al cliente (NULL si anónimo)","No","analytics@retailtech.co",365,"confidencial","FK"),
    ("eventos","session_id","VARCHAR(14)","Identificador de sesión web/app","No","analytics@retailtech.co",90,"interno",""),
    ("eventos","tipo_evento","VARCHAR(30)","Tipo de interacción digital","No","analytics@retailtech.co",365,"público",""),
    ("eventos","timestamp","TIMESTAMP","Fecha y hora exacta del evento","No","analytics@retailtech.co",365,"interno",""),
    ("eventos","producto_id","VARCHAR(10)","FK al producto (si aplica)","No","analytics@retailtech.co",365,"público","FK"),
    ("eventos","dispositivo","VARCHAR(20)","Tipo de dispositivo del usuario","No","analytics@retailtech.co",365,"público",""),
    ("eventos","pais","VARCHAR(50)","País del evento","No","analytics@retailtech.co",365,"público",""),
    ("eventos","duracion_seg","INTEGER","Duración de la interacción en segundos","No","analytics@retailtech.co",90,"público",""),
]

cols_dic = ["tabla","columna","tipo_dato","descripcion","es_pii","data_owner",
            "retencion_dias","clasificacion","constraint_tipo"]
df_dic = pd.DataFrame(diccionario, columns=cols_dic)
df_dic.to_csv(f"{OUTPUT_DIR}/diccionario_datos.csv", index=False)
print(f"  ✓ {len(df_dic)} entradas en el diccionario de datos")


# ─────────────────────────────────────────────
# RESUMEN FINAL
# ─────────────────────────────────────────────
print("\n" + "="*55)
print("  DATASET GENERADO EXITOSAMENTE")
print("="*55)
summary = {
    "clientes.csv":         len(df_clientes),
    "productos.csv":        len(df_productos),
    "pedidos.csv":          len(df_pedidos),
    "detalle_pedidos.csv":  len(df_detalles),
    "eventos.csv":          len(df_eventos),
    "diccionario_datos.csv":len(df_dic),
}
for f, n in summary.items():
    print(f"  {f:<28} {n:>6} registros")
print("="*55)
print("  Directorio de salida: ./data/")
print("="*55)

# Problemas de calidad intencionalmente introducidos (HINT para candidatos)
print("""
[INFO] Problemas de calidad introducidos intencionalmente:
  - ~5% de emails nulos en clientes
  - ~8% de teléfonos con valor 'N/A'
  - ~3% de ciudades en blanco
  - ~5% de stock_disponible nulos
  - ~2% de pedidos con pedido_id duplicado
  - ~30% de eventos sin cliente_id (sesiones anónimas)
  - ~5% de eventos sin duración (duracion_seg nulo)
""")
