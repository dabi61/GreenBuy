"""rename_user_table_to_users

Revision ID: fa1f2a1371b6
Revises: 88b411f0ac7d
Create Date: 2025-06-21 14:56:52.247649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa1f2a1371b6'
down_revision: Union[str, None] = '88b411f0ac7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename table from 'user' to 'users'
    op.rename_table('user', 'users')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename table back from 'users' to 'user'
    op.rename_table('users', 'user')
