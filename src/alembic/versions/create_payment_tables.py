"""create payment tables

Revision ID: payment_tables_001
Revises: 18d06b12a5d9
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'payment_tables_001'
down_revision = '18d06b12a5d9'
branch_labels = None
depends_on = None

def upgrade():
    # Create PaymentMethod table
    op.create_table(
        'payment_method',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('card_number', sa.String(), nullable=True),
        sa.Column('card_holder_name', sa.String(), nullable=True),
        sa.Column('expiry_month', sa.Integer(), nullable=True),
        sa.Column('expiry_year', sa.Integer(), nullable=True),
        sa.Column('paypal_email', sa.String(), nullable=True),
        sa.Column('bank_name', sa.String(), nullable=True),
        sa.Column('account_number', sa.String(), nullable=True),
        sa.Column('account_holder', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Payment table
    op.create_table(
        'payment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('payment_method_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, default='VND'),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('transaction_id', sa.String(), nullable=True),
        sa.Column('gateway_response', sa.String(), nullable=True),
        sa.Column('failure_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
        sa.ForeignKeyConstraint(['payment_method_id'], ['payment_method.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create RefundRequest table
    op.create_table(
        'refundrequest',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('admin_note', sa.String(), nullable=True),
        sa.Column('processed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['payment.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['processed_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Update Order table with new columns
    op.add_column('order', sa.Column('status', sa.String(), nullable=False, default='pending'))
    op.add_column('order', sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.add_column('order', sa.Column('confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('order', sa.Column('shipped_at', sa.DateTime(), nullable=True))
    op.add_column('order', sa.Column('delivered_at', sa.DateTime(), nullable=True))
    op.add_column('order', sa.Column('shipping_fee', sa.Float(), nullable=False, default=0.0))
    op.add_column('order', sa.Column('discount_amount', sa.Float(), nullable=False, default=0.0))
    op.add_column('order', sa.Column('final_amount', sa.Float(), nullable=False))
    op.add_column('order', sa.Column('shipping_address', sa.String(), nullable=True))
    op.add_column('order', sa.Column('shipping_phone', sa.String(), nullable=True))
    op.add_column('order', sa.Column('recipient_name', sa.String(), nullable=True))
    op.add_column('order', sa.Column('shipping_notes', sa.String(), nullable=True))
    op.add_column('order', sa.Column('tracking_number', sa.String(), nullable=True))
    op.add_column('order', sa.Column('admin_notes', sa.String(), nullable=True))
    op.add_column('order', sa.Column('cancellation_reason', sa.String(), nullable=True))
    
    # Update Product table with approval fields
    op.add_column('product', sa.Column('is_approved', sa.Boolean(), nullable=True))
    op.add_column('product', sa.Column('approval_note', sa.String(), nullable=True))
    op.add_column('product', sa.Column('approver_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_product_approver', 'product', 'user', ['approver_id'], ['id'])

def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_product_approver', 'product', type_='foreignkey')
    
    # Remove columns from Product table
    op.drop_column('product', 'approver_id')
    op.drop_column('product', 'approval_note')
    op.drop_column('product', 'is_approved')
    
    # Remove columns from Order table
    op.drop_column('order', 'cancellation_reason')
    op.drop_column('order', 'admin_notes')
    op.drop_column('order', 'tracking_number')
    op.drop_column('order', 'shipping_notes')
    op.drop_column('order', 'recipient_name')
    op.drop_column('order', 'shipping_phone')
    op.drop_column('order', 'shipping_address')
    op.drop_column('order', 'final_amount')
    op.drop_column('order', 'discount_amount')
    op.drop_column('order', 'shipping_fee')
    op.drop_column('order', 'delivered_at')
    op.drop_column('order', 'shipped_at')
    op.drop_column('order', 'confirmed_at')
    op.drop_column('order', 'updated_at')
    op.drop_column('order', 'status')
    
    # Drop tables
    op.drop_table('refundrequest')
    op.drop_table('payment')
    op.drop_table('payment_method') 