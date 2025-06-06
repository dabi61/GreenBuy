"""Replace is_buyer with role enum

Revision ID: 8953d55ec38b
Revises: 7ab9f1e0ed74
Create Date: 2025-06-06 21:53:44.858004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8953d55ec38b'
down_revision: Union[str, None] = '7ab9f1e0ed74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Tạo kiểu ENUM userrole
    user_role_enum = sa.Enum('buyer', 'seller', 'approve', name='userrole')
    user_role_enum.create(op.get_bind())

    # 2. Thêm cột mới role dùng ENUM vừa tạo
    op.add_column('user', sa.Column('role', user_role_enum, nullable=False, server_default='seller'))

    # 3. (Tuỳ chọn) Di chuyển dữ liệu từ is_buyer → role
    op.execute("UPDATE \"user\" SET role = 'buyer' WHERE is_buyer = TRUE;")
    op.execute("UPDATE \"user\" SET role = 'seller' WHERE is_buyer = FALSE;")

    # 4. Xoá cột is_buyer
    op.drop_column('user', 'is_buyer')

    # 5. (Không liên quan đến user) Nếu cần xoá bảng eventmodel thì giữ dòng sau:
    op.drop_table('eventmodel')

def downgrade() -> None:
    """Downgrade schema."""

    # 1. Thêm lại is_buyer
    op.add_column('user', sa.Column('is_buyer', sa.BOOLEAN(), nullable=True))

    # 2. Gán lại dữ liệu
    op.execute("UPDATE \"user\" SET is_buyer = TRUE WHERE role = 'buyer';")
    op.execute("UPDATE \"user\" SET is_buyer = FALSE WHERE role = 'seller';")

    # 3. Xoá cột role
    op.drop_column('user', 'role')

    # 4. Xoá enum userrole
    user_role_enum = sa.Enum('buyer', 'seller', 'approve', name='userrole')
    user_role_enum.drop(op.get_bind())

    # 5. Tạo lại bảng eventmodel nếu cần
    op.create_table(
        'eventmodel',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('page', sa.VARCHAR(), nullable=True),
        sa.Column('descriptions', sa.VARCHAR(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('update_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('eventmodel_user_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('eventmodel_pkey'))
    )
