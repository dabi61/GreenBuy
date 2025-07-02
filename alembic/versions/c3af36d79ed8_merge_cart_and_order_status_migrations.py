"""merge cart and order status migrations

Revision ID: c3af36d79ed8
Revises: cart_attribute_migration, ensure_order_status_column
Create Date: 2025-07-02 11:54:03.338271

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3af36d79ed8'
down_revision: Union[str, None] = ('cart_attribute_migration', 'ensure_order_status_column')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
