"""add avisos and acknowledgments tables

Revision ID: 0d1b2c3d4e5f
Revises: 0c1b2c3d4e5f
Create Date: 2026-06-12 14:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0d1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "0c1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "avisos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("alcance", sa.String(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("rol_destino", sa.String(), nullable=True),
        sa.Column("severidad", sa.String(), nullable=False, server_default=sa.text("'Info'")),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("inicio_en", sa.DateTime(), nullable=False),
        sa.Column("fin_en", sa.DateTime(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("requiere_ack", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"],),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "acknowledgments_aviso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("aviso_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("confirmado_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["aviso_id"], ["avisos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "aviso_id", "usuario_id",
            name="uix_ack_aviso_usuario",
        ),
    )


def downgrade() -> None:
    op.drop_table("acknowledgments_aviso")
    op.drop_table("avisos")
