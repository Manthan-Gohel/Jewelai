import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="owner")  # owner, manager, staff
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    instagram_accounts = relationship("InstagramAccount", back_populates="user", cascade="all, delete-orphan")


class InstagramAccount(Base):
    __tablename__ = "instagram_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ig_user_id = Column(String(100), unique=True, index=True, nullable=False)  # Meta Instagram Business Account ID
    username = Column(String(100), nullable=False)
    name = Column(String(255), nullable=True)
    profile_pic_url = Column(Text, nullable=True)
    token_encrypted = Column(Text, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_connected = Column(Boolean, default=True)
    webhook_subscribed = Column(Boolean, default=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="instagram_accounts")
    customers = relationship("Customer", back_populates="instagram_account", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="instagram_account", cascade="all, delete-orphan")
    settings = relationship("BusinessSettings", back_populates="instagram_account", uselist=False, cascade="all, delete-orphan")
    knowledge_docs = relationship("KnowledgeDocument", back_populates="instagram_account", cascade="all, delete-orphan")
    post_links = relationship("PostProductLink", back_populates="instagram_account", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    instagram_account_id = Column(String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    instagram_user_id = Column(String(100), nullable=False, index=True)  # IGSID (Instagram Scoped ID)
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    profile_pic_url = Column(Text, nullable=True)
    preferred_language = Column(String(10), default="en")
    notes = Column(Text, nullable=True)
    first_seen_at = Column(DateTime(timezone=True), default=utc_now)
    last_active_at = Column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index("idx_customer_account_ig_id", "instagram_account_id", "instagram_user_id", unique=True),
    )

    instagram_account = relationship("InstagramAccount", back_populates="customers")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    instagram_account_id = Column(String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="active")  # active, pending_human, resolved, closed
    ai_enabled = Column(Boolean, default=True)  # Conversation-specific AI toggle
    human_takeover = Column(Boolean, default=False)  # True when staff is actively intervening
    human_takeover_at = Column(DateTime(timezone=True), nullable=True)
    source_media_id = Column(String(100), nullable=True, index=True)  # Set when initiated via reel/post comment or share
    context_product_ids = Column(JSON, default=list)  # Linked products from source post/reel
    last_customer_message_at = Column(DateTime(timezone=True), nullable=True)  # Key for 24-hour window
    last_message_at = Column(DateTime(timezone=True), default=utc_now)
    unread_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    automation_logs = relationship("AutomationLog", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    meta_message_id = Column(String(200), unique=True, index=True, nullable=True)  # Meta 'mid'
    sender_type = Column(String(20), nullable=False)  # customer, ai, human
    message_type = Column(String(20), default="text")  # text, image, carousel, product_card
    content = Column(Text, nullable=True)
    media_urls = Column(JSON, default=list)  # list of media attachment URLs
    metadata_json = Column(JSON, default=dict)  # extracted intent, tokens, model info
    is_echo = Column(Boolean, default=False)
    delivery_status = Column(String(30), default="received")  # received, pending, sent, delivered, failed
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), default=utc_now)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    instagram_account_id = Column(String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # Rings, Necklaces, Earrings, Bangles, etc.
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    gold_purity = Column(String(50), nullable=True)  # 14K, 18K, 22K, 24K, 925 Silver, Platinum
    gross_weight = Column(Float, nullable=True)  # in grams
    net_weight = Column(Float, nullable=True)  # in grams
    diamond_specs = Column(JSON, nullable=True)  # {carat: 0.5, clarity: "VVS1", color: "F"}
    stock = Column(Integer, default=1)
    status = Column(String(50), default="active")  # active, draft, out_of_stock
    tags = Column(JSON, default=list)  # ["bridal", "traditional", "solitaire"]
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_product_account_sku", "instagram_account_id", "sku", unique=True),
    )

    instagram_account = relationship("InstagramAccount", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    storage_key = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False)
    alt_text = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    product = relationship("Product", back_populates="images")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    instagram_account_id = Column(String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), default="faq")  # faq, store_policy, gold_rates, shipping, custom_orders
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding_json = Column(JSON, nullable=True)  # vector representation
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    instagram_account = relationship("InstagramAccount", back_populates="knowledge_docs")


class BusinessSettings(Base):
    __tablename__ = "business_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    instagram_account_id = Column(String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(255), default="")
    tagline = Column(String(255), default="")
    default_language = Column(String(10), default="en")
    supported_languages = Column(JSON, default=lambda: ["en", "hi", "gu"])
    tone = Column(String(50), default="luxurious")  # elegant, luxurious, warm, formal
    system_prompt = Column(Text, nullable=True)
    auto_reply_enabled = Column(Boolean, default=False)
    require_human_escalation_for_negotiations = Column(Boolean, default=True)
    escalation_keywords = Column(JSON, default=lambda: ["discount", "bargain", "complaint", "talk to human", "manager", "phone", "owner", "ghatao", "vadhu discount"])
    contact_phone = Column(String(50), nullable=True)
    store_address = Column(Text, nullable=True)
    store_timings = Column(String(255), default="")
    # Zero represents an unconfigured rate, never a quoted market price.
    gold_rate_24k_per_10g = Column(Float, default=0.0)
    gold_rate_22k_per_10g = Column(Float, default=0.0)
    gold_rate_18k_per_10g = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    instagram_account = relationship("InstagramAccount", back_populates="settings")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    meta_event_id = Column(String(255), unique=True, index=True, nullable=True)
    event_type = Column(String(100), default="messages")
    payload_json = Column(JSON, nullable=False)
    signature_verified = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    received_at = Column(DateTime(timezone=True), default=utc_now)
    processed_at = Column(DateTime(timezone=True), nullable=True)


class AutomationLog(Base):
    __tablename__ = "automation_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), default="ai_reply")
    intent_detected = Column(String(100), nullable=True)
    language_detected = Column(String(20), nullable=True)
    retrieved_products_count = Column(Integer, default=0)
    ai_response_text = Column(Text, nullable=True)
    validation_passed = Column(Boolean, default=True)
    error_detail = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="automation_logs")


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    instagram_account_id = Column(String(36), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    request_type = Column(String(50), default="chat")  # chat, vision, embedding
    created_at = Column(DateTime(timezone=True), default=utc_now)


class PostProductLink(Base):
    __tablename__ = "post_product_links"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    instagram_account_id = Column(String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    media_id = Column(String(100), nullable=False, index=True)  # Meta Media ID / Reel ID
    media_type = Column(String(50), default="VIDEO")  # IMAGE, VIDEO, CAROUSEL_ALBUM
    permalink = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    product_ids = Column(JSON, default=list)  # List of linked Product IDs
    custom_reply_template = Column(Text, nullable=True)  # Optional custom reply text template
    auto_dm_enabled = Column(Boolean, default=True)  # Auto DM on comments
    public_reply_enabled = Column(Boolean, default=True)  # "Sent you a DM 📩"
    public_reply_text = Column(String(255), default="Sent you a DM with details! ✨")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_post_product_link_account_media", "instagram_account_id", "media_id", unique=True),
    )

    instagram_account = relationship("InstagramAccount", back_populates="post_links")


class ProcessedComment(Base):
    __tablename__ = "processed_comments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    instagram_account_id = Column(String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    comment_id = Column(String(100), unique=True, index=True, nullable=False)  # Meta comment_id
    media_id = Column(String(100), nullable=False, index=True)
    from_user_id = Column(String(100), nullable=False, index=True)
    from_username = Column(String(100), nullable=True)
    comment_text = Column(Text, nullable=False)
    intent = Column(String(50), default="inquiry")  # price, details, interested, general, spam
    private_reply_sent = Column(Boolean, default=False)
    public_reply_sent = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("idx_comment_account_created", "instagram_account_id", "created_at"),
    )
