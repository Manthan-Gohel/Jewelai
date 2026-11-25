from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, field_validator


# ==================== Auth & Users ====================
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    invite_code: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes.")
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Please enter your name.")
        return value.strip()


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== Instagram Account ====================
class InstagramAccountResponse(BaseModel):
    id: str
    ig_user_id: str
    username: str
    name: Optional[str] = None
    profile_pic_url: Optional[str] = None
    is_connected: bool
    webhook_subscribed: bool
    token_expires_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InstagramConnectRequest(BaseModel):
    code: str = Field(min_length=1, max_length=4096)
    state: str = Field(min_length=1, max_length=1024)
    redirect_uri: Optional[str] = None


class InstagramConnectTokenRequest(BaseModel):
    access_token: str


class CSVPreviewResponse(BaseModel):
    headers: List[str]
    sample_rows: List[Dict[str, Any]]
    suggested_mappings: Dict[str, str]
    total_preview_rows: int


class CSVImportMappedRequest(BaseModel):
    mapping: Dict[str, str]  # Standard field name -> CSV column header


# ==================== Customers ====================
class CustomerResponse(BaseModel):
    id: str
    instagram_user_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    profile_pic_url: Optional[str] = None
    preferred_language: str
    first_seen_at: datetime
    last_active_at: datetime

    class Config:
        from_attributes = True


# ==================== Messages & Conversations ====================
class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    meta_message_id: Optional[str] = None
    sender_type: str  # customer, ai, human
    message_type: str  # text, image, carousel, product_card
    content: Optional[str] = None
    media_urls: List[str] = []
    metadata_json: Dict[str, Any] = {}
    delivery_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class HumanReplyRequest(BaseModel):
    content: str
    media_url: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    customer: CustomerResponse
    status: str
    ai_enabled: bool
    human_takeover: bool
    last_customer_message_at: Optional[datetime] = None
    last_message_at: datetime
    unread_count: int
    latest_message: Optional[MessageResponse] = None

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    id: str
    customer: CustomerResponse
    status: str
    ai_enabled: bool
    human_takeover: bool
    last_customer_message_at: Optional[datetime] = None
    last_message_at: datetime
    unread_count: int
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationUpdateAI(BaseModel):
    ai_enabled: Optional[bool] = None
    human_takeover: Optional[bool] = None


# ==================== Products & Catalogue ====================
class ProductImageResponse(BaseModel):
    id: str
    image_url: str
    is_primary: bool
    alt_text: Optional[str] = None

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    description: Optional[str] = None
    price: float
    gold_purity: Optional[str] = "22K"
    gross_weight: Optional[float] = None
    net_weight: Optional[float] = None
    diamond_specs: Optional[Dict[str, Any]] = None
    stock: int = 1
    status: str = "active"
    tags: List[str] = []
    image_urls: List[str] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    gold_purity: Optional[str] = None
    gross_weight: Optional[float] = None
    net_weight: Optional[float] = None
    diamond_specs: Optional[Dict[str, Any]] = None
    stock: Optional[int] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None


class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    description: Optional[str] = None
    price: float
    gold_purity: Optional[str] = None
    gross_weight: Optional[float] = None
    net_weight: Optional[float] = None
    diamond_specs: Optional[Dict[str, Any]] = None
    stock: int
    status: str
    tags: List[str] = []
    images: List[ProductImageResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    categories: List[str] = []


# ==================== Knowledge & FAQs ====================
class KnowledgeDocCreate(BaseModel):
    category: str = "faq"
    title: str
    content: str
    is_active: bool = True


class KnowledgeDocUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeDocResponse(BaseModel):
    id: str
    category: str
    title: str
    content: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Business Settings ====================
class BusinessSettingsUpdate(BaseModel):
    business_name: Optional[str] = None
    tagline: Optional[str] = None
    default_language: Optional[str] = None
    supported_languages: Optional[List[str]] = None
    tone: Optional[str] = None
    system_prompt: Optional[str] = None
    auto_reply_enabled: Optional[bool] = None
    require_human_escalation_for_negotiations: Optional[bool] = None
    escalation_keywords: Optional[List[str]] = None
    contact_phone: Optional[str] = None
    store_address: Optional[str] = None
    store_timings: Optional[str] = None
    gold_rate_24k_per_10g: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    gold_rate_22k_per_10g: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    gold_rate_18k_per_10g: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("gold_rate_24k_per_10g", "gold_rate_22k_per_10g", "gold_rate_18k_per_10g", mode="before")
    @classmethod
    def clear_unknown_rate(cls, value):
        return 0 if value is None else value


class BusinessSettingsResponse(BaseModel):
    id: str
    business_name: str
    tagline: str
    default_language: str
    supported_languages: List[str]
    tone: str
    system_prompt: Optional[str] = None
    auto_reply_enabled: bool
    require_human_escalation_for_negotiations: bool
    escalation_keywords: List[str]
    contact_phone: Optional[str] = None
    store_address: Optional[str] = None
    store_timings: str
    gold_rate_24k_per_10g: float
    gold_rate_22k_per_10g: float
    gold_rate_18k_per_10g: float

    class Config:
        from_attributes = True


# ==================== AI Testing Playground ====================
class AITestRequest(BaseModel):
    message: str
    image_url: Optional[str] = None
    language_override: Optional[str] = None
    conversation_history: List[Dict[str, str]] = []


class AITestResponse(BaseModel):
    language_detected: str
    intent_detected: str
    extracted_entities: Dict[str, Any]
    retrieved_products: List[ProductResponse]
    retrieved_knowledge: List[KnowledgeDocResponse]
    generated_reply: str
    fact_validation_passed: bool
    validation_flags: List[str]
    confidence_score: float
    processing_time_ms: int


# ==================== Dashboard Analytics ====================
class DashboardOverviewMetrics(BaseModel):
    total_messages_today: int
    ai_replies_today: int
    pending_human_count: int
    ai_success_rate: float
    average_response_time_seconds: float
    active_conversations_count: int
    total_products_count: int
    connected_account_username: Optional[str] = None
    is_instagram_connected: bool


# ==================== Video / Post Product Linking ====================
class PostProductLinkCreate(BaseModel):
    media_id: str
    media_type: Optional[str] = "VIDEO"
    permalink: Optional[str] = None
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    product_ids: List[str] = []
    custom_reply_template: Optional[str] = None
    auto_dm_enabled: bool = True
    public_reply_enabled: bool = True
    public_reply_text: Optional[str] = "Sent you a DM with details! ✨"


class PostProductLinkUpdate(BaseModel):
    product_ids: Optional[List[str]] = None
    custom_reply_template: Optional[str] = None
    auto_dm_enabled: Optional[bool] = None
    public_reply_enabled: Optional[bool] = None
    public_reply_text: Optional[str] = None
    is_active: Optional[bool] = None


class PostProductLinkResponse(BaseModel):
    id: str
    instagram_account_id: str
    media_id: str
    media_type: str
    permalink: Optional[str] = None
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    product_ids: List[str] = []
    products: List[ProductResponse] = []
    custom_reply_template: Optional[str] = None
    auto_dm_enabled: bool
    public_reply_enabled: bool
    public_reply_text: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InstagramMediaItem(BaseModel):
    id: str
    caption: Optional[str] = None
    media_type: str
    media_url: Optional[str] = None
    permalink: Optional[str] = None
    thumbnail_url: Optional[str] = None
    timestamp: Optional[str] = None
    linked_product_ids: List[str] = []
    is_linked: bool = False
    auto_dm_enabled: bool = True


class ProcessedCommentResponse(BaseModel):
    id: str
    comment_id: str
    media_id: str
    from_username: Optional[str] = None
    comment_text: str
    intent: str
    private_reply_sent: bool
    public_reply_sent: bool
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
