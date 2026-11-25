"""Add post product links and processed comments

Revision ID: 002_post_product_links_and_comments
Revises: 001_initial_schema
Create Date: 2026-11-25 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_post_product_links_and_comments'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to conversations
    op.add_column('conversations', sa.Column('source_media_id', sa.String(length=100), nullable=True))
    op.add_column('conversations', sa.Column('context_product_ids', sa.JSON(), nullable=True))
    op.create_index('idx_conversations_source_media_id', 'conversations', ['source_media_id'])

    # Create post_product_links
    op.create_table(
        'post_product_links',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('instagram_account_id', sa.String(length=36), sa.ForeignKey('instagram_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('media_id', sa.String(length=100), nullable=False, index=True),
        sa.Column('media_type', sa.String(length=50), server_default='VIDEO'),
        sa.Column('permalink', sa.Text(), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('product_ids', sa.JSON(), nullable=True),
        sa.Column('custom_reply_template', sa.Text(), nullable=True),
        sa.Column('auto_dm_enabled', sa.Boolean(), server_default='true'),
        sa.Column('public_reply_enabled', sa.Boolean(), server_default='true'),
        sa.Column('public_reply_text', sa.String(length=255), server_default='Sent you a DM with details! ✨'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )
    op.create_index('idx_post_product_link_account_media', 'post_product_links', ['instagram_account_id', 'media_id'], unique=True)

    # Create processed_comments
    op.create_table(
        'processed_comments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('instagram_account_id', sa.String(length=36), sa.ForeignKey('instagram_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('comment_id', sa.String(length=100), unique=True, index=True, nullable=False),
        sa.Column('media_id', sa.String(length=100), index=True, nullable=False),
        sa.Column('from_user_id', sa.String(length=100), index=True, nullable=False),
        sa.Column('from_username', sa.String(length=100), nullable=True),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=50), server_default='inquiry'),
        sa.Column('private_reply_sent', sa.Boolean(), server_default='false'),
        sa.Column('public_reply_sent', sa.Boolean(), server_default='false'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )
    op.create_index('idx_comment_account_created', 'processed_comments', ['instagram_account_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('processed_comments')
    op.drop_table('post_product_links')
    op.drop_index('idx_conversations_source_media_id', table_name='conversations')
    op.drop_column('conversations', 'context_product_ids')
    op.drop_column('conversations', 'source_media_id')
