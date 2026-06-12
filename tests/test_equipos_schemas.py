import pytest
import uuid
from datetime import datetime, timezone
from pydantic import ValidationError
from app.schemas.equipos import (
    AsignacionMasivaRequest,
    ClonarRequest,
    ModificarVigenciaRequest,
)


class TestAsignacionMasivaRequest:

    def test_valid_request(self):
        data = {
            "asignaciones": [
                {
                    "user_id": str(uuid.uuid4()),
                    "role_id": 1,
                    "contexto_id": str(uuid.uuid4()),
                    "desde": "2025-03-01T00:00:00",
                }
            ]
        }
        req = AsignacionMasivaRequest(**data)
        assert len(req.asignaciones) == 1
        assert req.asignaciones[0].role_id == 1

    def test_multiple_asignaciones(self):
        data = {
            "asignaciones": [
                {
                    "user_id": str(uuid.uuid4()),
                    "role_id": 1,
                    "contexto_id": str(uuid.uuid4()),
                    "desde": "2025-03-01T00:00:00",
                }
                for _ in range(3)
            ]
        }
        req = AsignacionMasivaRequest(**data)
        assert len(req.asignaciones) == 3

    def test_empty_list_valid(self):
        data = {"asignaciones": []}
        req = AsignacionMasivaRequest(**data)
        assert len(req.asignaciones) == 0

    def test_invalid_uuid_raises(self):
        data = {
            "asignaciones": [
                {
                    "user_id": "not-a-uuid",
                    "role_id": 1,
                    "contexto_id": str(uuid.uuid4()),
                    "desde": "2025-03-01T00:00:00",
                }
            ]
        }
        with pytest.raises(ValidationError):
            AsignacionMasivaRequest(**data)


class TestClonarRequest:

    def test_valid_request(self):
        data = {
            "origen_contexto_id": str(uuid.uuid4()),
            "destino_contexto_id": str(uuid.uuid4()),
            "nuevo_desde": "2026-03-01T00:00:00",
            "nuevo_hasta": "2026-12-31T00:00:00",
        }
        req = ClonarRequest(**data)
        assert req.origen_contexto_id is not None
        assert req.nuevo_hasta is not None

    def test_without_hasta(self):
        data = {
            "origen_contexto_id": str(uuid.uuid4()),
            "destino_contexto_id": str(uuid.uuid4()),
            "nuevo_desde": "2026-03-01T00:00:00",
        }
        req = ClonarRequest(**data)
        assert req.nuevo_hasta is None

    def test_missing_origen_raises(self):
        data = {
            "destino_contexto_id": str(uuid.uuid4()),
            "nuevo_desde": "2026-03-01T00:00:00",
        }
        with pytest.raises(ValidationError):
            ClonarRequest(**data)


class TestModificarVigenciaRequest:

    def test_valid_request(self):
        data = {
            "contexto_id": str(uuid.uuid4()),
            "nuevo_desde": "2026-03-01T00:00:00",
            "nuevo_hasta": "2026-12-31T00:00:00",
        }
        req = ModificarVigenciaRequest(**data)
        assert req.nuevo_hasta is not None

    def test_without_hasta(self):
        data = {
            "contexto_id": str(uuid.uuid4()),
            "nuevo_desde": "2026-03-01T00:00:00",
        }
        req = ModificarVigenciaRequest(**data)
        assert req.nuevo_hasta is None

    def test_missing_contexto_raises(self):
        data = {
            "nuevo_desde": "2026-03-01T00:00:00",
        }
        with pytest.raises(ValidationError):
            ModificarVigenciaRequest(**data)
