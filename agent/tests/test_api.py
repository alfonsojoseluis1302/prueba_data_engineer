"""Tests de la API FastAPI."""

import pytest
from fastapi.testclient import TestClient
from agent.api import app

client = TestClient(app)


class TestHealth:
    def test_health_endpoint(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "duckdb_connected" in data
        assert "model" in data


class TestSessions:
    def test_create_session(self):
        response = client.post("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["message_count"] == 0

    def test_get_session(self):
        # Crear sesión
        create_resp = client.post("/api/sessions")
        session_id = create_resp.json()["session_id"]

        # Obtener sesión
        response = client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["session_id"] == session_id

    def test_get_nonexistent_session(self):
        response = client.get("/api/sessions/nonexistent-id")
        assert response.status_code == 404

    def test_delete_session(self):
        # Crear sesión
        create_resp = client.post("/api/sessions")
        session_id = create_resp.json()["session_id"]

        # Eliminar
        response = client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 200

        # Verificar eliminada
        response = client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 404


class TestSchemas:
    def test_list_schemas(self):
        response = client.get("/api/schemas")
        assert response.status_code == 200
        assert "tables" in response.json()
        assert len(response.json()["tables"]) > 0

    def test_get_schema(self):
        response = client.get("/api/schemas/pedidos")
        assert response.status_code == 200
        assert "pedidos" in response.json()["schema_info"]

    def test_get_schema_not_found(self):
        response = client.get("/api/schemas/no_existe")
        assert response.status_code == 404


class TestChat:
    def test_chat_requires_valid_session(self):
        response = client.post("/api/chat", json={
            "session_id": "invalid",
            "question": "Hola"
        })
        assert response.status_code == 404
