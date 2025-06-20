"""add_product_approval_columns

Revision ID: 88b411f0ac7d
Revises: 678854cb786e
Create Date: 2025-06-20 22:59:35.449154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88b411f0ac7d'
down_revision: Union[str, None] = 'c4d84a94399d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add approval columns to product table."""
    # Add approval columns to product table
    op.add_column('product', sa.Column('is_approved', sa.Boolean(), nullable=True))
    op.add_column('product', sa.Column('approval_note', sa.String(), nullable=True))
    op.add_column('product', sa.Column('approver_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'product_approver_id_fkey',
        'product',
        'user',
        ['approver_id'],
        ['id']
    )


def downgrade() -> None:
    """Remove approval columns from product table."""
    # Drop foreign key constraint first
    op.drop_constraint('product_approver_id_fkey', 'product', type_='foreignkey')
    
    # Drop the columns
    op.drop_column('product', 'approver_id')
    op.drop_column('product', 'approval_note')
    op.drop_column('product', 'is_approved')
