"""Convert order status from enum to integer

Revision ID: convert_status_to_integer
Revises: ensure_order_status_column
Create Date: 2025-06-27 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'convert_status_to_integer'
down_revision = '16da51923c42'
branch_labels = None
depends_on = None


def upgrade():
    """Convert status column from enum to integer"""
    # First, add a temporary integer column
    op.add_column('orders', sa.Column('status_int', sa.Integer(), nullable=True))
    
    # Convert enum values to integers
    op.execute("""
        UPDATE orders SET status_int = CASE 
            WHEN status = 'pending' THEN 1
            WHEN status = 'confirmed' THEN 2
            WHEN status = 'processing' THEN 3
            WHEN status = 'shipped' THEN 4
            WHEN status = 'delivered' THEN 5
            WHEN status = 'cancelled' THEN 6
            WHEN status = 'refunded' THEN 7
            WHEN status = 'returned' THEN 8
            ELSE 1
        END
    """)
    
    # Drop the old enum column
    op.drop_column('orders', 'status')
    
    # Rename the new column to status
    op.alter_column('orders', 'status_int', new_column_name='status')
    
    # Set default value and not null constraint
    op.alter_column('orders', 'status', nullable=False)
    op.execute("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 1")


def downgrade():
    """Convert status column back from integer to enum"""
    # This is complex, would need to recreate enum type
    # For now, just raise an error
    raise Exception("Downgrade not supported - this would require recreating enum type") 