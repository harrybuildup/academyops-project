"""add_role_to_users

Revision ID: 107785c425e3
Revises: 37f7f0b7f31d
Create Date: 2026-06-10 18:41:56.592907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '107785c425e3'
down_revision: Union[str, None] = '37f7f0b7f31d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    if 'users' in existing_tables:
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'role' not in columns:
            op.add_column('users', sa.Column('role', sa.String(length=20), server_default='Editor', nullable=False))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    if 'users' in existing_tables:
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'role' in columns:
            op.drop_column('users', 'role')
