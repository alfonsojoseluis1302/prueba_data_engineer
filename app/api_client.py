"""Cliente HTTP para la API del agente RetailTech."""

import os

import requests
from typing import Optional
from app.config import API_BASE_URL

TIMEOUT = int(os.getenv("CLIENT_TIMEOUT", "100"))  # Debe ser > CHAT_TIMEOUT del servidor (90s)


def check_health() -> dict:
    """Verifica el estado de la API."""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "ollama_connected": False, "duckdb_connected": False, "model": "N/A"}
    except Exception as e:
        return {"status": f"error: {e}", "ollama_connected": False, "duckdb_connected": False, "model": "N/A"}


def create_session() -> Optional[str]:
    """Crea una nueva sesión y retorna el session_id."""
    try:
        resp = requests.post(f"{API_BASE_URL}/api/sessions", timeout=10)
        resp.raise_for_status()
        return resp.json()["session_id"]
    except Exception:
        return None


def send_message(session_id: str, question: str) -> dict:
    """Envía una pregunta al agente."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={"session_id": session_id, "question": question},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"answer": "Timeout: la API tardó demasiado en responder. Intente de nuevo.", "reasoning_steps": [], "tools_used": [], "pii_filtered": False}
    except requests.exceptions.ConnectionError:
        return {"answer": "Error: no se pudo conectar con la API. Verifique que este corriendo (python run.py api).", "reasoning_steps": [], "tools_used": [], "pii_filtered": False}
    except Exception as e:
        return {"answer": f"Error: {e}", "reasoning_steps": [], "tools_used": [], "pii_filtered": False}


def get_history(session_id: str) -> dict:
    """Obtiene el historial de una sesión."""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/sessions/{session_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {"messages": []}
