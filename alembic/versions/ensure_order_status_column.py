"""ensure order status column exists

Revision ID: ensure_order_status_column
Revises: c4d84a94399d
Create Date: 2025-06-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ensure_order_status_column'
down_revision: Union[str, None] = 'c4d84a94399d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Check if orderstatus enum exists, if not create it
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'orderstatus'
        );
    """))
    
    enum_exists = result.scalar()
    
    if not enum_exists:
        # Create enum type
        orderstatus_enum = sa.Enum('PENDING', 'CONFIRMED', 'PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED', name='orderstatus')
        orderstatus_enum.create(op.get_bind())
    
    # Check if status column exists
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'order' AND column_name = 'status'
        );
    """))
    
    column_exists = result.scalar()
    
    if not column_exists:
        # Add status column
        op.add_column('order', sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED', name='orderstatus'), nullable=True))
        
        # Update existing orders to have default status
        op.execute("UPDATE \"order\" SET status = 'PENDING' WHERE status IS NULL")
        
        # Make status non-nullable after updating existing data
        op.alter_column('order', 'status', nullable=False)
    
    # Check and add other missing columns
    columns_to_check = [
        ('updated_at', sa.DateTime()),
        ('shipping_fee', sa.Float()),
        ('discount_amount', sa.Float()),
        ('final_amount', sa.Float()),
        ('shipping_address', sa.String()),
        ('shipping_phone', sa.String()),
        ('recipient_name', sa.String()),
        ('shipping_notes', sa.String())
    ]
    
    for column_name, column_type in columns_to_check:
        result = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'order' AND column_name = '{column_name}'
            );
        """))
        
        if not result.scalar():
            op.add_column('order', sa.Column(column_name, column_type, nullable=True))
            
            # Set default values for specific columns
            if column_name in ['shipping_fee', 'discount_amount']:
                op.execute(f"UPDATE \"order\" SET {column_name} = 0.0 WHERE {column_name} IS NULL")
                op.alter_column('order', column_name, nullable=False)
            elif column_name == 'updated_at':
                op.execute("UPDATE \"order\" SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
                op.alter_column('order', 'updated_at', nullable=False)
            elif column_name == 'final_amount':
                op.execute("UPDATE \"order\" SET final_amount = total_price WHERE final_amount IS NULL")
                op.alter_column('order', 'final_amount', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove added columns if they exist
    columns_to_remove = [
        'status', 'updated_at', 'shipping_fee', 'discount_amount', 
        'final_amount', 'shipping_address', 'shipping_phone', 
        'recipient_name', 'shipping_notes'
    ]
    
    for column_name in columns_to_remove:
        connection = op.get_bind()
        result = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'order' AND column_name = '{column_name}'
            );
        """))
        
        if result.scalar():
            op.drop_column('order', column_name) 