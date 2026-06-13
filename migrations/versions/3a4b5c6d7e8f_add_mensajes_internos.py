"""add mensajes_internos and perfil fields

Revision ID: 3a4b5c6d7e8f
Revises: 2a3b4c5d6e7f
Create Date: 2026-06-13 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "3a4b5c6d7e8f"
down_revision: Union[str, Sequence[str], None] = "2a3b4c5d6e7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("nombre", sa.String(), nullable=True))
    op.add_column("usuarios", sa.Column("datos_fiscales", sa.String(), nullable=True))
    op.add_column("usuarios", sa.Column("datos_bancarios", sa.String(), nullable=True))
    op.add_column("usuarios", sa.Column("regional", sa.String(), nullable=True))
    op.add_column("usuarios", sa.Column("modalidad_cobro", sa.String(), nullable=True))

    op.create_table(
        "mensajes_internos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("remitente_id", sa.Uuid(), nullable=False),
        sa.Column("destinatario_id", sa.Uuid(), nullable=False),
        sa.Column("asunto", sa.String(255), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("leido", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hilo_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["remitente_id"], ["usuarios.id"],),
        sa.ForeignKeyConstraint(["destinatario_id"], ["usuarios.id"],),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("mensajes_internos")
    op.drop_column("usuarios", "modalidad_cobro")
    op.drop_column("usuarios", "regional")
    op.drop_column("usuarios", "datos_bancarios")
    op.drop_column("usuarios", "datos_fiscales")
    op.drop_column("usuarios", "nombre")
