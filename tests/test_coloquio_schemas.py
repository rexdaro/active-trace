import pytest
import uuid
from datetime import datetime
from pydantic import ValidationError
from app.schemas.coloquio import (
    EvaluacionCreate,
    EvaluacionRead,
    ReservaCreate,
    ReservaRead,
    ReservaCancelResponse,
    ResultadoCreate,
    ResultadoRead,
    ImportAlumnosRequest,
    ImportAlumnosResponse,
    ConvovatoriaListItem,
    ConvocatoriaListResponse,
    PanelMetricas,
)


class TestEvaluacionCreate:
    def test_valid(self):
        data = EvaluacionCreate(
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            tipo="Parcial",
            instancia="2025-06-01",
        )
        assert data.cupos_por_dia == 10
        assert data.tipo == "Parcial"
        assert data.instancia == "2025-06-01"

    def test_cupos_por_dia_override(self):
        data = EvaluacionCreate(
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            tipo="TP",
            instancia="Primera",
            cupos_por_dia=5,
        )
        assert data.cupos_por_dia == 5


class TestReservaCreate:
    def test_valid(self):
        now = datetime(2025, 6, 1, 10, 0, 0)
        data = ReservaCreate(
            evaluacion_id=uuid.uuid4(),
            fecha_hora=now,
        )
        assert data.fecha_hora == now
        assert data.evaluacion_id is not None


class TestResultadoCreate:
    def test_valid(self):
        data = ResultadoCreate(
            evaluacion_id=uuid.uuid4(),
            alumno_id=uuid.uuid4(),
            nota_final="Aprobado",
        )
        assert data.nota_final == "Aprobado"


class TestImportAlumnosRequest:
    def test_valid(self):
        ev_id = uuid.uuid4()
        ids = [uuid.uuid4(), uuid.uuid4()]
        data = ImportAlumnosRequest(evaluacion_id=ev_id, alumno_ids=ids)
        assert data.evaluacion_id == ev_id
        assert len(data.alumno_ids) == 2

    def test_empty_list(self):
        data = ImportAlumnosRequest(
            evaluacion_id=uuid.uuid4(),
            alumno_ids=[],
        )
        assert data.alumno_ids == []


class TestImportAlumnosResponse:
    def test_valid(self):
        ev_id = uuid.uuid4()
        data = ImportAlumnosResponse(evaluacion_id=ev_id, cantidad=5)
        assert data.cantidad == 5


class TestPanelMetricas:
    def test_valid(self):
        data = PanelMetricas(
            total_evaluaciones=10,
            total_reservas_activas=25,
            total_resultados=15,
            total_alumnos_convocados=30,
        )
        assert data.total_evaluaciones == 10
        assert data.total_alumnos_convocados == 30


class TestReservaCancelResponse:
    def test_valid(self):
        rid = uuid.uuid4()
        data = ReservaCancelResponse(id=rid, estado="Cancelada")
        assert data.id == rid
        assert data.estado == "Cancelada"


class TestConvovatoriaListItem:
    def test_valid(self):
        now = datetime(2025, 6, 1, 10, 0, 0)
        data = ConvovatoriaListItem(
            id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            tipo="Parcial",
            instancia="Primera",
            cupos_por_dia=10,
            created_at=now,
        )
        assert data.materia_nombre == ""
        assert data.total_alumnos == 0
        assert data.reservas_activas == 0

    def test_with_metrics(self):
        now = datetime(2025, 6, 1, 10, 0, 0)
        data = ConvovatoriaListItem(
            id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            materia_nombre="Matemática",
            cohorte_id=uuid.uuid4(),
            tipo="TP",
            instancia="Segunda",
            cupos_por_dia=5,
            total_alumnos=20,
            reservas_activas=8,
            created_at=now,
        )
        assert data.materia_nombre == "Matemática"
        assert data.total_alumnos == 20
        assert data.reservas_activas == 8


class TestConvocatoriaListResponse:
    def test_valid(self):
        now = datetime(2025, 6, 1, 10, 0, 0)
        item = ConvovatoriaListItem(
            id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            tipo="Parcial",
            instancia="Primera",
            cupos_por_dia=10,
            created_at=now,
        )
        response = ConvocatoriaListResponse(items=[item], total=1)
        assert response.total == 1
        assert len(response.items) == 1


class TestEvaluacionReadFromAttributes:
    def test_from_attributes(self):
        class FakeEvaluacion:
            def __init__(self):
                self.id = uuid.uuid4()
                self.materia_id = uuid.uuid4()
                self.cohorte_id = uuid.uuid4()
                self.tipo = "Parcial"
                self.instancia = "2025-06-01"
                self.cupos_por_dia = 10
                self.created_at = datetime(2025, 6, 1, 10, 0, 0)

        ev = FakeEvaluacion()
        data = EvaluacionRead.model_validate(ev, from_attributes=True)
        assert data.id == ev.id
        assert data.materia_id == ev.materia_id
        assert data.cohorte_id == ev.cohorte_id
        assert data.tipo == "Parcial"
        assert data.instancia == "2025-06-01"
        assert data.cupos_por_dia == 10
        assert data.created_at == datetime(2025, 6, 1, 10, 0, 0)


class TestReservaReadFromAttributes:
    def test_from_attributes(self):
        class FakeReserva:
            def __init__(self):
                self.id = uuid.uuid4()
                self.evaluacion_id = uuid.uuid4()
                self.alumno_id = uuid.uuid4()
                self.fecha_hora = datetime(2025, 6, 10, 14, 0, 0)
                self.estado = "Activa"
                self.created_at = datetime(2025, 6, 1, 10, 0, 0)

        r = FakeReserva()
        data = ReservaRead.model_validate(r, from_attributes=True)
        assert data.id == r.id
        assert data.evaluacion_id == r.evaluacion_id
        assert data.alumno_id == r.alumno_id
        assert data.fecha_hora == datetime(2025, 6, 10, 14, 0, 0)
        assert data.estado == "Activa"
        assert data.created_at == datetime(2025, 6, 1, 10, 0, 0)


class TestResultadoReadFromAttributes:
    def test_from_attributes(self):
        class FakeResultado:
            def __init__(self):
                self.id = uuid.uuid4()
                self.evaluacion_id = uuid.uuid4()
                self.alumno_id = uuid.uuid4()
                self.nota_final = "9 (Nueve)"
                self.created_at = datetime(2025, 6, 15, 10, 0, 0)

        r = FakeResultado()
        data = ResultadoRead.model_validate(r, from_attributes=True)
        assert data.id == r.id
        assert data.evaluacion_id == r.evaluacion_id
        assert data.alumno_id == r.alumno_id
        assert data.nota_final == "9 (Nueve)"
        assert data.created_at == datetime(2025, 6, 15, 10, 0, 0)
