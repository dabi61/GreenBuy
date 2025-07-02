"""Fix address table columns

Revision ID: fix_address_columns
Revises: cart_attribute_migration
Create Date: 2024-12-28 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_address_columns'
down_revision = 'cart_attribute_migration'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to address table"""
    
    # Add missing columns
    op.add_column('address', sa.Column('street', sa.String(), nullable=True))
    op.add_column('address', sa.Column('state', sa.String(), nullable=True))
    op.add_column('address', sa.Column('zipcode', sa.String(), nullable=True))
    
    # Set default values for existing records (if any)
    op.execute("UPDATE address SET street = '' WHERE street IS NULL")
    op.execute("UPDATE address SET state = '' WHERE state IS NULL")
    op.execute("UPDATE address SET zipcode = '' WHERE zipcode IS NULL")
    
    # Make columns NOT NULL after setting defaults
    op.alter_column('address', 'street', nullable=False)
    op.alter_column('address', 'state', nullable=False)
    op.alter_column('address', 'zipcode', nullable=False)


def downgrade():
    """Remove the added columns"""
    op.drop_column('address', 'zipcode')
    op.drop_column('address', 'state')
    op.drop_column('address', 'street') 