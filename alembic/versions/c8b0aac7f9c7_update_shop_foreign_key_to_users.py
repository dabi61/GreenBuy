"""update_shop_foreign_key_to_users

Revision ID: c8b0aac7f9c7
Revises: fa1f2a1371b6
Create Date: 2025-06-21 14:59:01.085062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8b0aac7f9c7'
down_revision: Union[str, None] = 'fa1f2a1371b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old foreign key constraint
    op.drop_constraint('shop_user_id_fkey', 'shop', type_='foreignkey')
    
    # Create new foreign key constraint referencing 'users' table
    op.create_foreign_key('shop_user_id_fkey', 'shop', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the new foreign key constraint
    op.drop_constraint('shop_user_id_fkey', 'shop', type_='foreignkey')
    
    # Create old foreign key constraint referencing 'user' table
    op.create_foreign_key('shop_user_id_fkey', 'shop', 'user', ['user_id'], ['id'])
