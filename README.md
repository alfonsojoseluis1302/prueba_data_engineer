# RetailTech S.A.S — Prueba Tecnica Data Engineer

Pipeline ETL por capas (Bronze/Silver/Gold) con agente conversacional IA para e-commerce en 6 paises LATAM.

---

## Requisitos previos

| Requisito | Version minima | Verificar con |
|-----------|---------------|---------------|
| Python | 3.10+ | `python --version` |
| Git | cualquiera | `git --version` |

> **Ollama** se instala automaticamente al ejecutar `python run.py setup`. No es necesario instalarlo manualmente.

---

## Inicio rapido (un solo comando)

```bash
git clone <https://github.com/alfonsojoseluis1302/prueba_data_engineer.git>
cd prueba_data_engineer
python run.py setup      # venv + dependencias + Ollama + modelo LLM
python run.py pipeline   # ETL completo (Bronze -> Silver -> Gold)
python run.py doctor     # Verifica que todo esta OK
```

Eso es todo. El comando `setup` se encarga de:
1. Crear el entorno virtual en `.venv/`
2. Instalar dependencias Python desde `requirements.txt`
3. **Instalar Ollama** si no esta presente (Windows/Linux/macOS)
4. **Iniciar el servidor** Ollama si no esta corriendo
5. **Descargar el modelo** `llama3.2` (~2 GB) si no esta disponible

---

## Guia paso a paso

### Paso 1: Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd prueba_data_engineer
```

### Paso 2: Setup completo (automatizado)

```bash
python run.py setup
```

> **Modelo recomendado**: `llama3.2:3b` — cabe en GPUs de 4 GB (ej: GTX 1650). Para usar otro modelo: `set OLLAMA_MODEL=llama3.2:1b` antes del setup.

### Paso 3: Diagnostico del sistema

```bash
python run.py doctor
```

Verifica: plataforma, Python, venv, Ollama (binario + servidor + modelo) y DuckDB.

### Paso 4: Ejecutar el pipeline ETL

```bash
python run.py pipeline
```

El pipeline ejecuta 4 fases en orden:

| Fase | Que hace | Output |
|------|----------|--------|
| **Bronze** | Copia CSVs -> Parquet con metadatos | `pipeline/data/bronze/*.parquet` |
| **Silver** | Limpieza + enmascaramiento PII | `pipeline/data/silver/*.parquet` |
| **Gold** | Agregaciones analiticas + DuckDB | `pipeline/data/gold/*.parquet` |
| **Queries** | 12 consultas SQL de negocio | Resultados en consola |

### Paso 5: Ejecutar tests

```bash
python run.py test
```

Esperado: 30 tests passed.

### Paso 6: Levantar la API del agente (Terminal 1)

```bash
python run.py api
```

La API se levanta en `http://localhost:8000`. El servidor Ollama se inicia automaticamente si no esta corriendo.

Verificar salud:
```bash
curl -X GET http://localhost:8000/api/health
```

### Paso 7: Levantar Streamlit (Terminal 2)

En otra terminal:

```bash
python run.py app
```

Abre el navegador en `http://localhost:8501`.

---

## Comandos disponibles

| Comando | Descripcion |
|---------|-------------|
| `python run.py setup` | Instalar todo (venv + deps + Ollama + modelo) |
| `python run.py doctor` | Diagnostico completo del sistema |
| `python run.py pipeline` | Ejecutar ETL completo |
| `python run.py pipeline bronze` | Solo capa Bronze |
| `python run.py pipeline silver` | Solo capa Silver |
| `python run.py pipeline gold` | Solo capa Gold |
| `python run.py api` | Iniciar FastAPI (port 8000) |
| `python run.py app` | Iniciar Streamlit (port 8501) |
| `python run.py test` | Ejecutar pytest |
| `python run.py lint` | Verificacion de sintaxis |
| `python run.py clean` | Limpiar datos generados |

> En macOS/Linux tambien puedes usar `make <target>` como alternativa.

---

## Variables de entorno opcionales

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2` | Modelo LLM a usar |
| `LLM_TIMEOUT` | `60` | Timeout en segundos para llamadas al LLM |
| `CHAT_TIMEOUT` | `90` | Timeout del endpoint /api/chat |

---

## Troubleshooting

### `python: command not found`
Instala Python 3.10+ desde [python.org](https://www.python.org/downloads/).

### El setup falla al instalar Ollama en Windows
Si la instalacion automatica falla, descarga manualmente desde [ollama.com](https://ollama.com) y vuelve a ejecutar `python run.py setup`.

### `ConnectionRefusedError` al usar el agente
El servidor Ollama no esta corriendo. El comando `python run.py api` intenta iniciarlo automaticamente. Si falla, ejecuta `ollama serve` manualmente en otra terminal.

### Timeout al hacer preguntas al agente
- Verifica que Ollama este corriendo: `ollama list`
- El modelo `llama3.2:3b` es el recomendado para hardware limitado
- La primera pregunta puede tardar mas (warmup del modelo)
- Ajusta el timeout: `set LLM_TIMEOUT=120`

### `ModuleNotFoundError`
Las dependencias no estan instaladas. Ejecuta `python run.py setup`.

---

## Arquitectura

```
DataSource/ (CSVs originales)
    |
    v
pipeline/data/raw/          <- Copia inmutable
    |
    v Bronze (ingesta + metadatos)
pipeline/data/bronze/       <- Parquet, sin correcciones
    |
    v Silver (limpieza + PII masking)
pipeline/data/silver/       <- Parquet, datos limpios
    |
    v Gold (agregaciones analiticas)
pipeline/data/gold/         <- Parquet + DuckDB
    |
    v
agent/ (FastAPI + Ollama)   <- API REST con agente ReAct
    |
    v
app/ (Streamlit)            <- Frontend del agente
```

## Estructura del proyecto

```
├── DataSource/              # CSVs originales + generador
├── pipeline/
│   ├── src/                 # Modulos del pipeline
│   │   ├── io_utils.py      # Rutas y lectura/escritura
│   │   ├── db_loader.py     # Conexion DuckDB
│   │   ├── profiling.py     # Perfilado de datos
│   │   ├── bronze.py        # Capa Bronze
│   │   ├── quality_rules.py # Reglas de calidad
│   │   ├── cleaning.py      # Funciones de limpieza
│   │   ├── masking.py       # Enmascaramiento PII
│   │   ├── silver.py        # Capa Silver
│   │   ├── gold.py          # Capa Gold
│   │   └── sql_runner.py    # Ejecutor de queries SQL
│   ├── data/                # Datos por capa
│   ├── queries.sql          # 12 queries de negocio
│   └── pipeline.py          # CLI principal
├── agent/
│   ├── api.py               # FastAPI backend (async)
│   ├── agent.py             # Agente ReAct
│   ├── llm_backend.py       # Abstraccion LLM cross-platform
│   ├── tools.py             # Herramientas del agente
│   ├── guardrails.py        # Proteccion PII
│   ├── memory.py            # Gestion de sesiones
│   ├── schemas.py           # Modelos Pydantic
│   ├── prompts/             # System prompt + few shots
│   ├── tests/               # Tests del agente
│   └── governance/          # Documentacion de gobernanza
├── app/
│   ├── main.py              # Interfaz Streamlit
│   ├── api_client.py        # Cliente HTTP para la API
│   └── config.py            # Configuracion y colores
├── run.py                   # CLI cross-platform (automatiza todo)
├── Makefile                 # Alternativa para macOS/Linux
├── requirements.txt         # Dependencias Python
└── pyproject.toml           # Configuracion pytest
```

## Governance

- **Catalogo de datos:** `agent/governance/catalog.md`
- **Linaje de datos:** `agent/governance/lineage.md`
- **Politica PII:** `agent/governance/pii_policy.md`
- **Acceso del agente:** `agent/governance/agent_access.md`
