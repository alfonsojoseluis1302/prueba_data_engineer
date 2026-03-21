"""Gestión de sesiones de conversación del agente."""

import uuid
from datetime import datetime, timedelta
from typing import Optional


class SessionManager:
    """Gestiona sesiones de conversación in-memory."""

    def __init__(self, max_messages: int = 20, ttl_minutes: int = 60):
        self._sessions: dict[str, dict] = {}
        self.max_messages = max_messages
        self.ttl_minutes = ttl_minutes

    def create_session(self) -> str:
        """Crea una nueva sesión y retorna su ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now(),
            "messages": [],
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Retorna una sesión si existe y no ha expirado."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        # Verificar TTL
        if datetime.now() - session["last_activity"] > timedelta(minutes=self.ttl_minutes):
            del self._sessions[session_id]
            return None

        return session

    def add_message(self, session_id: str, role: str, content: str):
        """Agrega un mensaje a la sesión."""
        session = self.get_session(session_id)
        if not session:
            return

        session["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

        # Limitar historial
        if len(session["messages"]) > self.max_messages:
            session["messages"] = session["messages"][-self.max_messages:]

        session["last_activity"] = datetime.now()

    def get_messages(self, session_id: str) -> list[dict]:
        """Retorna el historial de mensajes de una sesión."""
        session = self.get_session(session_id)
        if not session:
            return []
        return session["messages"]

    def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> list[dict]:
        """Lista todas las sesiones activas."""
        self._cleanup_expired()
        return [
            {
                "session_id": sid,
                "created_at": data["created_at"],
                "message_count": len(data["messages"]),
            }
            for sid, data in self._sessions.items()
        ]

    def _cleanup_expired(self):
        """Limpia sesiones expiradas."""
        now = datetime.now()
        expired = [
            sid for sid, data in self._sessions.items()
            if now - data["last_activity"] > timedelta(minutes=self.ttl_minutes)
        ]
        for sid in expired:
            del self._sessions[sid]
