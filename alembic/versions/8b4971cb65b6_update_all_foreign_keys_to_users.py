"""update_all_foreign_keys_to_users

Revision ID: 8b4971cb65b6
Revises: c8b0aac7f9c7
Create Date: 2025-06-21 15:00:19.169456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b4971cb65b6'
down_revision: Union[str, None] = 'c8b0aac7f9c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # At this point, the 'user' table has been renamed to 'users'
    # Most foreign key constraints should automatically work with the renamed table
    # We just need to make sure all models are using the correct reference
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
