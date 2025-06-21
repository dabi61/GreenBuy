"""fix_shop_foreign_key_constraint

Revision ID: c5ffb2eba4b3
Revises: 8b4971cb65b6
Create Date: 2025-06-21 15:01:54.285065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5ffb2eba4b3'
down_revision: Union[str, None] = '8b4971cb65b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check and drop the existing foreign key constraint if it exists
    connection = op.get_bind()
    
    # Check if constraint exists
    result = connection.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'shop' 
        AND constraint_name = 'shop_user_id_fkey'
        AND constraint_type = 'FOREIGN KEY'
    """))
    
    constraint_exists = result.fetchone() is not None
    
    if constraint_exists:
        # Drop the existing constraint
        op.drop_constraint('shop_user_id_fkey', 'shop', type_='foreignkey')
    
    # Create new foreign key constraint pointing to 'users' table
    op.create_foreign_key(
        'shop_user_id_fkey', 
        'shop', 
        'users', 
        ['user_id'], 
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the current constraint
    op.drop_constraint('shop_user_id_fkey', 'shop', type_='foreignkey')
    
    # Create constraint pointing back to 'user' table
    op.create_foreign_key(
        'shop_user_id_fkey', 
        'shop', 
        'user', 
        ['user_id'], 
        ['id']
    )
