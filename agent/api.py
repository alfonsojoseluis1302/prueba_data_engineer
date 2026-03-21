"""FastAPI backend para el agente conversacional RetailTech."""

import asyncio
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

CHAT_TIMEOUT = int(os.getenv("CHAT_TIMEOUT", "90"))

from agent.schemas import (
    ChatRequest, ChatResponse, SessionResponse, HealthResponse, SchemaResponse,
)
from agent.agent import RetailTechAgent
from agent.memory import SessionManager
from agent.tools import ejecutar_sql, obtener_esquema, ALLOWED_TABLES

app = FastAPI(
    title="RetailTech Agent API",
    description="API REST del agente conversacional analítico de RetailTech S.A.S",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancias globales
model = os.getenv("OLLAMA_MODEL", "llama3.2")
agent = RetailTechAgent(model=model)
sessions = SessionManager(max_messages=20, ttl_minutes=60)


@app.on_event("startup")
async def warmup():
    """Warm up LLM connection on startup."""
    try:
        agent._llm.call([{"role": "user", "content": "test"}])
        logger.info("LLM warmup complete")
    except Exception as e:
        logger.warning("LLM warmup failed (server will still start): %s", e)


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Health check: verifica conexion a Ollama/MLX y DuckDB."""
    llm_ok = agent._llm.is_healthy()
    duckdb_ok = False

    try:
        from pipeline.src.db_loader import get_connection
        con = get_connection()
        con.execute("SELECT 1")
        con.close()
        duckdb_ok = True
    except Exception:
        pass

    status = "healthy" if (llm_ok and duckdb_ok) else "degraded"
    return HealthResponse(
        status=status,
        ollama_connected=llm_ok,
        duckdb_connected=duckdb_ok,
        model=model,
    )


@app.post("/api/sessions", response_model=SessionResponse)
def create_session():
    """Crea una nueva sesión de conversación."""
    session_id = sessions.create_session()
    session = sessions.get_session(session_id)
    return SessionResponse(
        session_id=session_id,
        created_at=session["created_at"],
        message_count=0,
        messages=[],
    )


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    """Obtiene el historial de una sesión."""
    session = sessions.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    return SessionResponse(
        session_id=session_id,
        created_at=session["created_at"],
        message_count=len(session["messages"]),
        messages=session["messages"],
    )


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    """Elimina una sesión."""
    if not sessions.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return {"detail": "Sesión eliminada"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Envia una pregunta al agente (async con timeout)."""
    session = sessions.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")

    history = sessions.get_messages(request.session_id)
    sessions.add_message(request.session_id, "user", request.question)

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(agent.chat, request.question, history),
            timeout=CHAT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        result = {
            "answer": "La consulta excedio el tiempo maximo del servidor. Intente una pregunta mas simple.",
            "reasoning_steps": [],
            "tools_used": [],
            "pii_filtered": False,
        }

    sessions.add_message(request.session_id, "assistant", result["answer"])
    return ChatResponse(**result)


@app.get("/api/schemas")
def list_schemas():
    """Lista las tablas disponibles."""
    return {"tables": sorted(ALLOWED_TABLES)}


@app.get("/api/schemas/{table}", response_model=SchemaResponse)
def get_schema(table: str):
    """Obtiene el esquema de una tabla."""
    if table not in ALLOWED_TABLES:
        raise HTTPException(status_code=404, detail=f"Tabla '{table}' no encontrada")

    schema = obtener_esquema(table)
    return SchemaResponse(table=table, schema_info=schema)
