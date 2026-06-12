import pytest
import uuid
from datetime import date, datetime
from pydantic import ValidationError
from app.schemas.encuentro import (
    SlotEncuentroRead,
    InstanciaEncuentroUpdate,
    RecurrenteRequest,
    RecurrenteResponse,
    GuardiaRead,
)


class TestRecurrenteRequest:
    def test_cant_semanas_must_be_at_least_1(self):
        with pytest.raises(ValidationError) as exc:
            RecurrenteRequest(
                materia_id=uuid.uuid4(),
                dia_semana="Lunes",
                horario="10:00",
                titulo="Clase 1",
                fecha_inicio=date(2025, 3, 1),
                cant_semanas=0,
            )
        errors = exc.value.errors()
        assert any("cant_semanas" in e["loc"] for e in errors)

    def test_cant_semanas_negative(self):
        with pytest.raises(ValidationError):
            RecurrenteRequest(
                materia_id=uuid.uuid4(),
                dia_semana="Lunes",
                horario="10:00",
                titulo="Clase 1",
                fecha_inicio=date(2025, 3, 1),
                cant_semanas=-1,
            )

    def test_valid_recurrente_request(self):
        req = RecurrenteRequest(
            materia_id=uuid.uuid4(),
            dia_semana="Martes",
            horario="14:00",
            titulo="Lab",
            fecha_inicio=date(2025, 3, 1),
            cant_semanas=16,
        )
        assert req.cant_semanas == 16
        assert req.dia_semana == "Martes"
        assert req.materia_id is not None
        assert req.meet_url is None

    def test_valid_with_meet_url(self):
        req = RecurrenteRequest(
            materia_id=uuid.uuid4(),
            dia_semana="Lunes",
            horario="18:00",
            titulo="Clase 1",
            meet_url="https://meet.google.com/abc",
            fecha_inicio=date(2025, 3, 1),
            cant_semanas=1,
        )
        assert req.cant_semanas == 1
        assert req.meet_url == "https://meet.google.com/abc"


class TestInstanciaEncuentroUpdate:
    def test_all_fields_optional(self):
        update = InstanciaEncuentroUpdate()
        assert update.estado is None
        assert update.meet_url is None
        assert update.video_url is None
        assert update.comentario is None

    def test_partial_fields(self):
        update = InstanciaEncuentroUpdate(
            estado="Realizado",
            video_url="https://youtu.be/abc",
        )
        assert update.estado == "Realizado"
        assert update.video_url == "https://youtu.be/abc"
        assert update.meet_url is None
        assert update.comentario is None

    def test_all_fields(self):
        update = InstanciaEncuentroUpdate(
            estado="Cancelado",
            meet_url="https://meet.google.com/new",
            video_url="https://youtu.be/xyz",
            comentario="Se cancela por feriado",
        )
        assert update.estado == "Cancelado"
        assert update.meet_url == "https://meet.google.com/new"
        assert update.video_url == "https://youtu.be/xyz"
        assert update.comentario == "Se cancela por feriado"


class TestSlotEncuentroReadFromAttributes:
    def test_from_attributes(self):
        class FakeSlot:
            def __init__(self):
                self.id = uuid.uuid4()
                self.materia_id = uuid.uuid4()
                self.creado_por = uuid.uuid4()
                self.dia_semana = "Lunes"
                self.horario = "18:00"
                self.titulo = "Clase 1"
                self.meet_url = "https://meet.google.com/abc"
                self.fecha_inicio = date(2025, 3, 1)
                self.cant_semanas = 16
                self.activo = True
                self.created_at = datetime(2025, 3, 1, 10, 0, 0)

        slot = FakeSlot()
        data = SlotEncuentroRead.model_validate(slot, from_attributes=True)
        assert data.id == slot.id
        assert data.materia_id == slot.materia_id
        assert data.creado_por == slot.creado_por
        assert data.dia_semana == "Lunes"
        assert data.horario == "18:00"
        assert data.titulo == "Clase 1"
        assert data.meet_url == "https://meet.google.com/abc"
        assert data.fecha_inicio == date(2025, 3, 1)
        assert data.cant_semanas == 16
        assert data.activo is True
        assert data.created_at == datetime(2025, 3, 1, 10, 0, 0)

    def test_from_attributes_meet_url_none(self):
        class FakeSlot:
            def __init__(self):
                self.id = uuid.uuid4()
                self.materia_id = uuid.uuid4()
                self.creado_por = uuid.uuid4()
                self.dia_semana = "Martes"
                self.horario = "14:00"
                self.titulo = "Lab"
                self.meet_url = None
                self.fecha_inicio = date(2025, 3, 1)
                self.cant_semanas = 16
                self.activo = True
                self.created_at = datetime(2025, 3, 1, 10, 0, 0)

        slot = FakeSlot()
        data = SlotEncuentroRead.model_validate(slot, from_attributes=True)
        assert data.meet_url is None


class TestGuardiaReadFromAttributes:
    def test_from_attributes(self):
        class FakeGuardia:
            def __init__(self):
                self.id = uuid.uuid4()
                self.asignacion_id = uuid.uuid4()
                self.materia_id = uuid.uuid4()
                self.carrera_id = uuid.uuid4()
                self.cohorte_id = uuid.uuid4()
                self.dia = "Lunes"
                self.horario = "18:00"
                self.estado = "Pendiente"
                self.comentarios = "Sin novedades"
                self.created_at = datetime(2025, 3, 1, 10, 0, 0)

        guardia = FakeGuardia()
        data = GuardiaRead.model_validate(guardia, from_attributes=True)
        assert data.id == guardia.id
        assert data.dia == "Lunes"
        assert data.estado == "Pendiente"
        assert data.comentarios == "Sin novedades"

    def test_from_attributes_comentarios_none(self):
        class FakeGuardia:
            def __init__(self):
                self.id = uuid.uuid4()
                self.asignacion_id = uuid.uuid4()
                self.materia_id = uuid.uuid4()
                self.carrera_id = uuid.uuid4()
                self.cohorte_id = uuid.uuid4()
                self.dia = "Martes"
                self.horario = "14:00"
                self.estado = "Realizada"
                self.comentarios = None
                self.created_at = datetime(2025, 3, 1, 10, 0, 0)

        guardia = FakeGuardia()
        data = GuardiaRead.model_validate(guardia, from_attributes=True)
        assert data.comentarios is None


class TestRecurrenteResponse:
    def test_recurrente_response(self):
        now = datetime(2025, 3, 1, 10, 0, 0)
        slot = SlotEncuentroRead(
            id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            creado_por=uuid.uuid4(),
            dia_semana="Lunes",
            horario="18:00",
            titulo="Clase 1",
            meet_url=None,
            fecha_inicio=date(2025, 3, 1),
            cant_semanas=16,
            activo=True,
            created_at=now,
        )
        response = RecurrenteResponse(slot=slot, instancias_count=16)
        assert response.instancias_count == 16
        assert response.slot.titulo == "Clase 1"
