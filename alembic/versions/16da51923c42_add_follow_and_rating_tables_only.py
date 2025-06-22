"""add follow and rating tables only

Revision ID: 16da51923c42
Revises: c5ffb2eba4b3
Create Date: 2025-06-22 22:45:45.372645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16da51923c42'
down_revision: Union[str, None] = 'c5ffb2eba4b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User Follow Table
    op.create_table('user_follows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('follower_id', sa.Integer(), nullable=False),
        sa.Column('following_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['following_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('follower_id', 'following_id', name='unique_user_follow')
    )
    op.create_index(op.f('ix_user_follows_follower_id'), 'user_follows', ['follower_id'], unique=False)
    op.create_index(op.f('ix_user_follows_following_id'), 'user_follows', ['following_id'], unique=False)

    # Shop Follow Table
    op.create_table('shop_follows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['shop_id'], ['shop.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'shop_id', name='unique_shop_follow')
    )
    op.create_index(op.f('ix_shop_follows_user_id'), 'shop_follows', ['user_id'], unique=False)
    op.create_index(op.f('ix_shop_follows_shop_id'), 'shop_follows', ['shop_id'], unique=False)

    # User Rating Table
    op.create_table('user_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rater_id', sa.Integer(), nullable=False),
        sa.Column('rated_user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='user_rating_range'),
        sa.ForeignKeyConstraint(['rater_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['rated_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rater_id', 'rated_user_id', name='unique_user_rating')
    )
    op.create_index(op.f('ix_user_ratings_rater_id'), 'user_ratings', ['rater_id'], unique=False)
    op.create_index(op.f('ix_user_ratings_rated_user_id'), 'user_ratings', ['rated_user_id'], unique=False)
    op.create_index(op.f('ix_user_ratings_rating'), 'user_ratings', ['rating'], unique=False)

    # Shop Rating Table
    op.create_table('shop_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='shop_rating_range'),
        sa.ForeignKeyConstraint(['shop_id'], ['shop.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'shop_id', name='unique_shop_rating')
    )
    op.create_index(op.f('ix_shop_ratings_user_id'), 'shop_ratings', ['user_id'], unique=False)
    op.create_index(op.f('ix_shop_ratings_shop_id'), 'shop_ratings', ['shop_id'], unique=False)
    op.create_index(op.f('ix_shop_ratings_rating'), 'shop_ratings', ['rating'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_shop_ratings_rating'), table_name='shop_ratings')
    op.drop_index(op.f('ix_shop_ratings_shop_id'), table_name='shop_ratings')
    op.drop_index(op.f('ix_shop_ratings_user_id'), table_name='shop_ratings')
    op.drop_table('shop_ratings')
    
    op.drop_index(op.f('ix_user_ratings_rating'), table_name='user_ratings')
    op.drop_index(op.f('ix_user_ratings_rated_user_id'), table_name='user_ratings')
    op.drop_index(op.f('ix_user_ratings_rater_id'), table_name='user_ratings')
    op.drop_table('user_ratings')
    
    op.drop_index(op.f('ix_shop_follows_shop_id'), table_name='shop_follows')
    op.drop_index(op.f('ix_shop_follows_user_id'), table_name='shop_follows')
    op.drop_table('shop_follows')
    
    op.drop_index(op.f('ix_user_follows_following_id'), table_name='user_follows')
    op.drop_index(op.f('ix_user_follows_follower_id'), table_name='user_follows')
    op.drop_table('user_follows')
