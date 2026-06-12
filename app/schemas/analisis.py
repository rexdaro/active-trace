import uuid
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class AlumnoAtrasado(BaseModel):
    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None = None
    regional: str | None = None
    actividades_faltantes: list[str] = []
    actividades_desaprobadas: list[str] = []
    motivo: str


class AtrasadosResponse(BaseModel):
    atrasados: list[AlumnoAtrasado]
    total: int

    model_config = ConfigDict(from_attributes=True)


class RankingEntry(BaseModel):
    posicion: int
    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None = None
    actividades_aprobadas: int
    total_actividades: int


class RankingResponse(BaseModel):
    ranking: list[RankingEntry]
    total: int

    model_config = ConfigDict(from_attributes=True)


class ActividadReporte(BaseModel):
    actividad: str
    total: int
    aprobados: int
    no_aprobados: int
    porcentaje_aprobacion: float


class ReporteMateria(BaseModel):
    sin_datos: bool = False
    total_alumnos: int = 0
    total_actividades: int = 0
    total_calificaciones: int = 0
    aprobados: int = 0
    no_aprobados: int = 0
    porcentaje_aprobacion: float = 0.0
    por_actividad: list[ActividadReporte] = []

    model_config = ConfigDict(from_attributes=True)


class EstadoSinDatos(BaseModel):
    sin_datos: bool = True
    mensaje: str = "No hay calificaciones para esta materia"


class NotaFinalAlumno(BaseModel):
    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None = None
    promedio: float
    actividades_count: int

    model_config = ConfigDict(from_attributes=True)


class ActividadTextual(BaseModel):
    actividad: str
    nota_textual: str


class NotaFinalTextual(BaseModel):
    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None = None
    actividades: list[ActividadTextual] = []

    model_config = ConfigDict(from_attributes=True)


class NotasFinalesResponse(BaseModel):
    notas_numericas: list[NotaFinalAlumno] = []
    notas_textuales: list[NotaFinalTextual] = []

    model_config = ConfigDict(from_attributes=True)


class MonitorMateria(BaseModel):
    materia_id: uuid.UUID
    materia_nombre: str
    total_actividades: int
    aprobadas: int
    no_aprobadas: int
    faltantes: int


class MonitorAlumno(BaseModel):
    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None
    materias: list[MonitorMateria] = []

    model_config = ConfigDict(from_attributes=True)


class MonitorGeneralResponse(BaseModel):
    alumnos: list[MonitorAlumno] = []
    total: int
    filtros_aplicados: dict = {}

    model_config = ConfigDict(from_attributes=True)


class SeguimientoAlumno(BaseModel):
    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None
    actividades_totales: int = 0
    aprobadas: int = 0
    no_aprobadas: int = 0
    faltantes: int = 0
    pct_cumplimiento: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class SeguimientoResponse(BaseModel):
    alumnos: list[SeguimientoAlumno] = []
    total: int

    model_config = ConfigDict(from_attributes=True)
