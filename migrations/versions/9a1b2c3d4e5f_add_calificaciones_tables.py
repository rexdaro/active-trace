"""add calificaciones tables

Revision ID: 9a1b2c3d4e5f
Revises: 8a1b2c3d4e5f
Create Date: 2026-06-12 11:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "9a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "8a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calificaciones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("entrada_padron_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("actividad", sa.String(), nullable=False),
        sa.Column("nota_numerica", sa.Numeric(5, 2), nullable=True),
        sa.Column("nota_textual", sa.String(), nullable=True),
        sa.Column("aprobado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("origen", sa.String(), nullable=False),
        sa.Column("importado_por", sa.Uuid(), nullable=True),
        sa.Column("importado_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["entrada_padron_id"], ["entradas_padron.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"],),
        sa.ForeignKeyConstraint(["importado_por"], ["usuarios.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "entrada_padron_id", "actividad", "materia_id",
            name="uix_calif_entrada_actividad",
        ),
    )
    op.create_table(
        "umbrales_materia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("umbral_pct", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("valores_aprobatorios", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignaciones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "asignacion_id", "materia_id",
            name="uix_umbral_asignacion_materia",
        ),
    )


def downgrade() -> None:
    op.drop_table("umbrales_materia")
    op.drop_table("calificaciones")
