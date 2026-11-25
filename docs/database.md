# JewelAI — PostgreSQL Database Specification

## 1. Schema Design Principles
1. **Account-Level Multi-Tenant Isolation**: Every customer, conversation, product, knowledge document, and log entry is keyed to an `instagram_account_id`.
2. **Instagram Scoped IDs (IGSID)**: Customers are identified by Meta's official Instagram-scoped user ID (`instagram_user_id`), ensuring accurate conversation matching even when public usernames change.
3. **Strict Idempotency**: Meta Message IDs (`meta_message_id`) have unique constraints to prevent duplicate deliveries.
4. **Token Encryption at Rest**: Instagram access tokens are stored using authenticated Fernet encryption. Preserve and back up `ENCRYPTION_KEY`; losing it makes existing encrypted tokens unreadable. Fernet is not AES-GCM.

---

## 2. Table Specifications

### `users`
- `id`: VARCHAR(36) PRIMARY KEY
- `name`: VARCHAR(255)
- `email`: VARCHAR(255) UNIQUE INDEX
- `password_hash`: VARCHAR(255) (bcrypt)
- `role`: VARCHAR(50) (owner, manager, staff)
- `is_active`: BOOLEAN

### `instagram_accounts`
- `id`: VARCHAR(36) PRIMARY KEY
- `user_id`: VARCHAR(36) FOREIGN KEY -> users.id (CASCADE)
- `ig_user_id`: VARCHAR(100) UNIQUE INDEX (Meta Professional Account ID)
- `username`: VARCHAR(100)
- `name`: VARCHAR(255)
- `token_encrypted`: TEXT (Encrypted long-lived access token)
- `token_expires_at`: TIMESTAMPTZ
- `is_connected`: BOOLEAN
- `webhook_subscribed`: BOOLEAN

### `customers`
- `id`: VARCHAR(36) PRIMARY KEY
- `instagram_account_id`: VARCHAR(36) FOREIGN KEY -> instagram_accounts.id
- `instagram_user_id`: VARCHAR(100) INDEX (IGSID)
- `username`: VARCHAR(100)
- `full_name`: VARCHAR(255)
- `preferred_language`: VARCHAR(10) (en, hi, gu)
- Unique composite index: `(instagram_account_id, instagram_user_id)`

### `conversations`
- `id`: VARCHAR(36) PRIMARY KEY
- `customer_id`: VARCHAR(36) FOREIGN KEY -> customers.id
- `instagram_account_id`: VARCHAR(36) FOREIGN KEY -> instagram_accounts.id
- `status`: VARCHAR(50) (active, pending_human, resolved)
- `ai_enabled`: BOOLEAN (Thread-level AI toggle)
- `human_takeover`: BOOLEAN
- `human_takeover_at`: TIMESTAMPTZ
- `last_customer_message_at`: TIMESTAMPTZ (Key field for Meta 24-hour window)
- `unread_count`: INTEGER

### `messages`
- `id`: VARCHAR(36) PRIMARY KEY
- `conversation_id`: VARCHAR(36) FOREIGN KEY -> conversations.id
- `meta_message_id`: VARCHAR(200) UNIQUE INDEX (`mid`)
- `sender_type`: VARCHAR(20) (customer, ai, human)
- `message_type`: VARCHAR(20) (text, image, carousel)
- `content`: TEXT
- `media_urls`: JSON (array of URLs)
- `metadata_json`: JSON (intent, language, matched SKU, latency)
- `delivery_status`: VARCHAR(30) (received, pending, sent, failed)

### `products`
- `id`: VARCHAR(36) PRIMARY KEY
- `instagram_account_id`: VARCHAR(36) FOREIGN KEY -> instagram_accounts.id
- `sku`: VARCHAR(100) INDEX
- `name`: VARCHAR(255)
- `category`: VARCHAR(100) (Rings, Necklaces, Earrings, Bangles, etc.)
- `description`: TEXT
- `price`: FLOAT (verified in INR)
- `gold_purity`: VARCHAR(50) (14K, 18K, 22K, 24K, Platinum)
- `gross_weight`: FLOAT (grams)
- `net_weight`: FLOAT (grams)
- `diamond_specs`: JSON ({carat, clarity, color})
- `stock`: INTEGER
- `status`: VARCHAR(50) (active, draft, out_of_stock)

### `knowledge_documents`
- `id`: VARCHAR(36) PRIMARY KEY
- `instagram_account_id`: VARCHAR(36) FOREIGN KEY -> instagram_accounts.id
- `category`: VARCHAR(100) (faq, store_policy, gold_rates, shipping, custom_orders)
- `title`: VARCHAR(255)
- `content`: TEXT
- `is_active`: BOOLEAN

### `business_settings`
- `id`: VARCHAR(36) PRIMARY KEY
- `instagram_account_id`: VARCHAR(36) FOREIGN KEY -> instagram_accounts.id UNIQUE
- `business_name`: VARCHAR(255)
- `tagline`: VARCHAR(255)
- `tone`: VARCHAR(50) (luxurious, elegant, warm)
- `auto_reply_enabled`: BOOLEAN
- `gold_rate_24k_per_10g`: FLOAT
- `gold_rate_22k_per_10g`: FLOAT
- `gold_rate_18k_per_10g`: FLOAT
- `store_address`: TEXT
- `store_timings`: VARCHAR(255)

### `webhook_events`
- `id`: VARCHAR(36) PRIMARY KEY
- `meta_event_id`: VARCHAR(255) INDEX
- `event_type`: VARCHAR(100)
- `payload_json`: JSON
- `signature_verified`: BOOLEAN
- `processed`: BOOLEAN
- `received_at`: TIMESTAMPTZ
- `processed_at`: TIMESTAMPTZ

### `automation_logs`
- `id`: VARCHAR(36) PRIMARY KEY
- `conversation_id`: VARCHAR(36) FOREIGN KEY -> conversations.id
- `action`: VARCHAR(100)
- `intent_detected`: VARCHAR(100)
- `language_detected`: VARCHAR(20)
- `retrieved_products_count`: INTEGER
- `ai_response_text`: TEXT
- `validation_passed`: BOOLEAN
- `latency_ms`: INTEGER
