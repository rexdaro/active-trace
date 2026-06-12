"""add evaluaciones y coloquios tables

Revision ID: 0c1b2c3d4e5f
Revises: 0b1b2c3d4e5f
Create Date: 2026-06-12 13:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0c1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "0b1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluaciones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("instancia", sa.String(), nullable=False),
        sa.Column("cupos_por_dia", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"],),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reservas_evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False, server_default=sa.text("'Activa'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuarios.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "evaluacion_id", "alumno_id",
            name="uix_reserva_alumno_evaluacion",
        ),
    )
    op.create_index(
        "ix_reservas_fecha",
        "reservas_evaluacion",
        ["tenant_id", "evaluacion_id", "fecha_hora"],
    )
    op.create_table(
        "resultados_evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("nota_final", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuarios.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "evaluacion_id", "alumno_id",
            name="uix_resultado_alumno_evaluacion",
        ),
    )


def downgrade() -> None:
    op.drop_table("resultados_evaluacion")
    op.drop_index("ix_reservas_fecha", table_name="reservas_evaluacion")
    op.drop_table("reservas_evaluacion")
    op.drop_table("evaluaciones")
