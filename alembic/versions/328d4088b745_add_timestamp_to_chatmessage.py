"""add timestamp to chatmessage

Revision ID: 328d4088b745
Revises: 3a7c64c7c38e
Create Date: 2025-06-08 22:55:35.706487

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '328d4088b745'
down_revision: Union[str, None] = '3a7c64c7c38e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Xóa bảng eventmodel
    op.drop_table('eventmodel')

    # 1. Thêm cột timestamp với nullable=True để tránh lỗi với dữ liệu cũ
    op.add_column('chatmessage', sa.Column('timestamp', sa.DateTime(), nullable=True))

    # 2. Cập nhật timestamp cho các bản ghi hiện có (dùng datetime.utcnow())
    op.execute(
        f"UPDATE chatmessage SET timestamp = '{datetime.utcnow().isoformat(sep=' ', timespec='seconds')}'"
    )

    # 3. Thay đổi cột timestamp thành NOT NULL sau khi đã cập nhật
    op.alter_column('chatmessage', 'timestamp', nullable=False)

    # 4. Xoá cột created_at
    op.drop_column('chatmessage', 'created_at')


def downgrade() -> None:
    """Downgrade schema."""
    # Thêm lại cột created_at
    op.add_column('chatmessage', sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))

    # Xóa cột timestamp
    op.drop_column('chatmessage', 'timestamp')

    # Tạo lại bảng eventmodel
    op.create_table(
        'eventmodel',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('page', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('descriptions', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column('update_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('eventmodel_user_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('eventmodel_pkey'))
    )
