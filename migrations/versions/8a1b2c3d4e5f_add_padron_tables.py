"""add padron tables

Revision ID: 8a1b2c3d4e5f
Revises: 814fd5c777fb
Create Date: 2026-06-12 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '814fd5c777fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('versiones_padron',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('materia_id', sa.Uuid(), nullable=False),
        sa.Column('cohorte_id', sa.Uuid(), nullable=False),
        sa.Column('archivo_nombre', sa.String(), nullable=False),
        sa.Column('archivo_hash', sa.String(), nullable=False),
        sa.Column('origen', sa.String(), nullable=False),
        sa.Column('cargado_por', sa.Uuid(), nullable=False),
        sa.Column('activa', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['materia_id'], ['materias.id'], ),
        sa.ForeignKeyConstraint(['cohorte_id'], ['cohortes.id'], ),
        sa.ForeignKeyConstraint(['cargado_por'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.create_index(
            'uix_versiones_padron_activa',
            'versiones_padron',
            ['tenant_id', 'materia_id', 'cohorte_id'],
            unique=True,
            postgresql_where=sa.text('activa = true'),
        )
    op.create_table('entradas_padron',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('version_id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('usuario_id', sa.Uuid(), nullable=True),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('apellidos', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('comision', sa.String(), nullable=True),
        sa.Column('regional', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['versiones_padron.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.add_column('tenants', sa.Column('moodle_ws_url', sa.String(), nullable=True))
    op.add_column('tenants', sa.Column('moodle_token', sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.drop_index('uix_versiones_padron_activa')
    op.drop_table('entradas_padron')
    op.drop_table('versiones_padron')
    op.drop_column('tenants', 'moodle_token')
    op.drop_column('tenants', 'moodle_ws_url')
