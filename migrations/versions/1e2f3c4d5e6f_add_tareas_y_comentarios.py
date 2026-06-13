"""add tareas and comentarios_tarea tables

Revision ID: 1e2f3c4d5e6f
Revises: 0d1b2c3d4e5f
Create Date: 2026-06-12 16:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "1e2f3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "0d1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tareas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("asignado_a", sa.Uuid(), nullable=False),
        sa.Column("asignado_por", sa.Uuid(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False, server_default=sa.text("'Pendiente'")),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("contexto_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"],),
        sa.ForeignKeyConstraint(["asignado_a"], ["usuarios.id"],),
        sa.ForeignKeyConstraint(["asignado_por"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "comentarios_tarea",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("tarea_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["tarea_id"], ["tareas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["autor_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("comentarios_tarea")
    op.drop_table("tareas")
