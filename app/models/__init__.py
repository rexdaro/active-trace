from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User  # Usuario is User (backward-compat alias)
from app.models.asignacion import Asignacion
from app.models.token import RefreshToken
from app.models.rbac import Role, Permission, RolePermission
from app.models.user_role import UserRole
from app.models.audit import AuditLog
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.padron import VersionPadron, EntradaPadron
from app.models.calificacion import Calificacion, CalificacionOrigen
from app.models.umbral_materia import UmbralMateria
from app.models.comunicacion import Comunicacion, ComunicacionEstado
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro, EstadoInstancia
from app.models.guardia import Guardia, EstadoGuardia
from app.models.coloquio import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion, TipoEvaluacion, EstadoReserva
from app.models.aviso import Aviso, AcknowledgmentAviso, AlcanceAviso, SeveridadAviso
from app.models.tarea import Tarea, ComentarioTarea, EstadoTarea
from app.models.programa_materia import ProgramaMateria
from app.models.fecha_academica import FechaAcademica, TipoFecha
from app.models.salario import SalarioBase, SalarioPlus
from app.models.liquidacion import Liquidacion, Factura, EstadoLiquidacion, EstadoFactura
from app.models.mensaje_interno import MensajeInterno
