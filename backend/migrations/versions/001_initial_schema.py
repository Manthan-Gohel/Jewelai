"""Initial schema creation for JewelAI

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-21 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='owner'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )

    # Instagram Accounts
    op.create_table(
        'instagram_accounts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('ig_user_id', sa.String(length=100), nullable=False, unique=True, index=True),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('profile_pic_url', sa.Text(), nullable=True),
        sa.Column('token_encrypted', sa.Text(), nullable=False),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_connected', sa.Boolean(), server_default='true'),
        sa.Column('webhook_subscribed', sa.Boolean(), server_default='false'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )

    # Customers
    op.create_table(
        'customers',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('instagram_account_id', sa.String(length=36), sa.ForeignKey('instagram_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('instagram_user_id', sa.String(length=100), nullable=False, index=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('profile_pic_url', sa.Text(), nullable=True),
        sa.Column('preferred_language', sa.String(length=10), server_default='en'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True)),
        sa.Column('last_active_at', sa.DateTime(timezone=True))
    )

    # Conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('customer_id', sa.String(length=36), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('instagram_account_id', sa.String(length=36), sa.ForeignKey('instagram_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('status', sa.String(length=50), server_default='active'),
        sa.Column('ai_enabled', sa.Boolean(), server_default='true'),
        sa.Column('human_takeover', sa.Boolean(), server_default='false'),
        sa.Column('human_takeover_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_customer_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True)),
        sa.Column('unread_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )

    # Messages
    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('meta_message_id', sa.String(length=200), nullable=True, unique=True, index=True),
        sa.Column('sender_type', sa.String(length=20), nullable=False),
        sa.Column('message_type', sa.String(length=20), server_default='text'),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('media_urls', sa.JSON(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('is_echo', sa.Boolean(), server_default='false'),
        sa.Column('delivery_status', sa.String(length=30), server_default='received'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )

    # Products
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('instagram_account_id', sa.String(length=36), sa.ForeignKey('instagram_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sku', sa.String(length=100), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('gold_purity', sa.String(length=50), nullable=True),
        sa.Column('gross_weight', sa.Float(), nullable=True),
        sa.Column('net_weight', sa.Float(), nullable=True),
        sa.Column('diamond_specs', sa.JSON(), nullable=True),
        sa.Column('stock', sa.Integer(), server_default='1'),
        sa.Column('status', sa.String(length=50), server_default='active'),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )

    # Product Images
    op.create_table(
        'product_images',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('image_url', sa.Text(), nullable=False),
        sa.Column('storage_key', sa.String(length=255), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default='false'),
        sa.Column('alt_text', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )

    # Knowledge Documents
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('instagram_account_id', sa.String(length=36), sa.ForeignKey('instagram_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('category', sa.String(length=100), server_default='faq'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding_json', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )

    # Business Settings
    op.create_table(
        'business_settings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('instagram_account_id', sa.String(length=36), sa.ForeignKey('instagram_accounts.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('business_name', sa.String(length=255), server_default='Luxe Aura Jewels'),
        sa.Column('tagline', sa.String(length=255), server_default='Timeless Elegance & Certified Fine Jewellery'),
        sa.Column('default_language', sa.String(length=10), server_default='en'),
        sa.Column('supported_languages', sa.JSON(), nullable=True),
        sa.Column('tone', sa.String(length=50), server_default='luxurious'),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('auto_reply_enabled', sa.Boolean(), server_default='true'),
        sa.Column('require_human_escalation_for_negotiations', sa.Boolean(), server_default='true'),
        sa.Column('escalation_keywords', sa.JSON(), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('store_address', sa.Text(), nullable=True),
        sa.Column('store_timings', sa.String(length=255), nullable=True),
        sa.Column('gold_rate_24k_per_10g', sa.Float(), server_default='78500.0'),
        sa.Column('gold_rate_22k_per_10g', sa.Float(), server_default='72000.0'),
        sa.Column('gold_rate_18k_per_10g', sa.Float(), server_default='58900.0'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )

    # Webhook Events
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('meta_event_id', sa.String(length=255), nullable=True, unique=True, index=True),
        sa.Column('event_type', sa.String(length=100), server_default='messages'),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('signature_verified', sa.Boolean(), server_default='false'),
        sa.Column('processed', sa.Boolean(), server_default='false'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True)),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Automation Logs
    op.create_table(
        'automation_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('action', sa.String(length=100), server_default='ai_reply'),
        sa.Column('intent_detected', sa.String(length=100), nullable=True),
        sa.Column('language_detected', sa.String(length=20), nullable=True),
        sa.Column('retrieved_products_count', sa.Integer(), server_default='0'),
        sa.Column('ai_response_text', sa.Text(), nullable=True),
        sa.Column('validation_passed', sa.Boolean(), server_default='true'),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )

    # Usage Records
    op.create_table(
        'usage_records',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('instagram_account_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('input_tokens', sa.Integer(), server_default='0'),
        sa.Column('output_tokens', sa.Integer(), server_default='0'),
        sa.Column('estimated_cost', sa.Float(), server_default='0.0'),
        sa.Column('request_type', sa.String(length=50), server_default='chat'),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )


def downgrade() -> None:
    op.drop_table('usage_records')
    op.drop_table('automation_logs')
    op.drop_table('webhook_events')
    op.drop_table('business_settings')
    op.drop_table('knowledge_documents')
    op.drop_table('product_images')
    op.drop_table('products')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('customers')
    op.drop_table('instagram_accounts')
    op.drop_table('users')
