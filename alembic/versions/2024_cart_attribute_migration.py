"""Change cart from product_id to attribute_id

Revision ID: cart_attribute_migration
Revises: convert_status_to_integer
Create Date: 2024-12-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cart_attribute_migration'
down_revision = 'convert_status_to_integer'
branch_labels = None
depends_on = None


def upgrade():
    """Change CartItem from product_id to attribute_id"""
    
    # Step 1: Add new column attribute_id (nullable first to avoid issues)
    op.add_column('cartitem', sa.Column('attribute_id', sa.Integer(), nullable=True))
    
    # Step 2: Clear existing cart data to avoid foreign key issues
    # (This is necessary because we can't easily migrate product_id to attribute_id)
    op.execute("DELETE FROM cartitem")
    
    # Step 3: Make attribute_id NOT NULL now that table is empty
    op.alter_column('cartitem', 'attribute_id', nullable=False)
    
    # Step 4: Add foreign key constraint for attribute_id
    op.create_foreign_key(
        'fk_cartitem_attribute_id', 
        'cartitem', 
        'attribute', 
        ['attribute_id'], 
        ['attribute_id']
    )
    
    # Step 5: Drop old foreign key constraint for product_id
    op.drop_constraint('cartitem_product_id_fkey', 'cartitem', type_='foreignkey')
    
    # Step 6: Drop old product_id column
    op.drop_column('cartitem', 'product_id')


def downgrade():
    """Revert CartItem back to product_id from attribute_id"""
    
    # Step 1: Add back product_id column
    op.add_column('cartitem', sa.Column('product_id', sa.Integer(), nullable=True))
    
    # Step 2: Clear cart data (can't reverse the migration easily)
    op.execute("DELETE FROM cartitem")
    
    # Step 3: Make product_id NOT NULL
    op.alter_column('cartitem', 'product_id', nullable=False)
    
    # Step 4: Add foreign key constraint for product_id
    op.create_foreign_key(
        'cartitem_product_id_fkey',
        'cartitem', 
        'product', 
        ['product_id'], 
        ['product_id']
    )
    
    # Step 5: Drop attribute_id foreign key constraint
    op.drop_constraint('fk_cartitem_attribute_id', 'cartitem', type_='foreignkey')
    
    # Step 6: Drop attribute_id column
    op.drop_column('cartitem', 'attribute_id') 