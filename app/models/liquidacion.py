from __future__ import annotations
import uuid
import enum
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Text, Boolean, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class EstadoLiquidacion(str, enum.Enum):
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class EstadoFactura(str, enum.Enum):
    PENDIENTE = "Pendiente"
    ABONADA = "Abonada"


class Liquidacion(Base, TimestampMixin, TenantMixin):
    __tablename__ = "liquidaciones"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohortes.id"), nullable=False)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    rol: Mapped[str] = mapped_column(String, nullable=False)
    comisiones: Mapped[str | None] = mapped_column(Text, nullable=True)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    monto_plus: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    es_nexo: Mapped[bool] = mapped_column(Boolean, default=False)
    excluido_por_factura: Mapped[bool] = mapped_column(Boolean, default=False)
    estado: Mapped[str] = mapped_column(String, default=EstadoLiquidacion.ABIERTA.value)


class Factura(Base, TimestampMixin, TenantMixin):
    __tablename__ = "facturas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    referencia_archivo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tamano_kb: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estado: Mapped[str] = mapped_column(String, default=EstadoFactura.PENDIENTE.value)
    abonada_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
