"""add encuentros y guardias tables

Revision ID: 0b1b2c3d4e5f
Revises: 0a1b2c3d4e5f
Create Date: 2026-06-12 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0b1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "0a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "slots_encuentro",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("creado_por", sa.Uuid(), nullable=False),
        sa.Column("dia_semana", sa.String(), nullable=False),
        sa.Column("horario", sa.String(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("meet_url", sa.String(), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("cant_semanas", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"],),
        sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "instancias_encuentro",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("slot_id", sa.Uuid(), nullable=True),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.String(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False, server_default=sa.text("'Programado'")),
        sa.Column("meet_url", sa.String(), nullable=True),
        sa.Column("video_url", sa.String(), nullable=True),
        sa.Column("comentario", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["slot_id"], ["slots_encuentro.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_instancias_materia_fecha", "instancias_encuentro", ["tenant_id", "materia_id", "fecha"])
    op.create_table(
        "guardias",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("carrera_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("dia", sa.String(), nullable=False),
        sa.Column("horario", sa.String(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False, server_default=sa.text("'Pendiente'")),
        sa.Column("comentarios", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignaciones.id"],),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"],),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"],),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"],),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("guardias")
    op.drop_index("ix_instancias_materia_fecha", table_name="instancias_encuentro")
    op.drop_table("instancias_encuentro")
    op.drop_table("slots_encuentro")
