"""add_custom_fields

Revision ID: a1b2c3d4e5f6
Revises: 107785c425e3
Create Date: 2026-06-27 18:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '107785c425e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Create custom_field_definitions table
    if 'custom_field_definitions' not in existing_tables:
        op.create_table('custom_field_definitions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('field_key', sa.String(length=100), nullable=False),
            sa.Column('field_type', sa.String(length=20), nullable=False),
            sa.Column('options', sa.JSON(), nullable=True),
            sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_custom_field_definitions_field_key'), 'custom_field_definitions', ['field_key'], unique=True)

    # Add custom_fields column to leads table
    if 'leads' in existing_tables:
        columns = [c['name'] for c in inspector.get_columns('leads')]
        if 'custom_fields' not in columns:
            op.add_column('leads', sa.Column('custom_fields', sa.JSON(), server_default='{}', nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Remove custom_fields column from leads
    if 'leads' in existing_tables:
        columns = [c['name'] for c in inspector.get_columns('leads')]
        if 'custom_fields' in columns:
            op.drop_column('leads', 'custom_fields')

    # Drop custom_field_definitions table
    if 'custom_field_definitions' in existing_tables:
        op.drop_index(op.f('ix_custom_field_definitions_field_key'), table_name='custom_field_definitions')
        op.drop_table('custom_field_definitions')
