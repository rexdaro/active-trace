"""add comunicaciones tables

Revision ID: 0a1b2c3d4e5f
Revises: 9a1b2c3d4e5f
Create Date: 2026-06-12 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "9a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("requiere_aprobacion", sa.Boolean(), server_default=sa.text("0"), nullable=False),
    )
    op.create_table(
        "comunicaciones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("enviado_por", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("destinatario", sa.String(), nullable=False),
        sa.Column("asunto", sa.String(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False, server_default=sa.text("'Pendiente'")),
        sa.Column("lote_id", sa.Uuid(), nullable=True),
        sa.Column("lote_aprobado", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("enviado_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],),
        sa.ForeignKeyConstraint(["enviado_por"], ["usuarios.id"],),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_comunicaciones_tenant_lote",
        "comunicaciones",
        ["tenant_id", "lote_id"],
    )
    op.create_index(
        "ix_comunicaciones_tenant_estado",
        "comunicaciones",
        ["tenant_id", "estado"],
    )


def downgrade() -> None:
    op.drop_index("ix_comunicaciones_tenant_estado", table_name="comunicaciones")
    op.drop_index("ix_comunicaciones_tenant_lote", table_name="comunicaciones")
    op.drop_table("comunicaciones")
    op.drop_column("tenants", "requiere_aprobacion")
