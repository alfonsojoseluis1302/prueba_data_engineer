"""Modelos Pydantic para la API del agente."""

from pydantic import BaseModel, ConfigDict
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str
    question: str


class ReasoningStep(BaseModel):
    iteration: int
    type: str
    content: Optional[str] = None
    tool: Optional[str] = None
    args: Optional[dict] = None
    result: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    reasoning_steps: list[dict] = []
    tools_used: list[str] = []
    pii_filtered: bool = False


class SessionResponse(BaseModel):
    session_id: str
    created_at: Optional[str] = None
    message_count: int = 0
    messages: list[dict] = []


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    duckdb_connected: bool
    model: str


class SchemaResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    table: str
    schema_info: str


class ErrorResponse(BaseModel):
    detail: str
