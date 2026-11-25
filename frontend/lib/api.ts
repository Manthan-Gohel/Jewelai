const API_BASE = "/api/v1";

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface InstagramAccount {
  id: string;
  username: string;
  is_connected: boolean;
  webhook_subscribed: boolean;
  token_expires_at?: string | null;
}

export interface InstagramStatus {
  account: InstagramAccount | null;
  login_available: boolean;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export interface OverviewMetrics {
  total_messages_today: number;
  ai_replies_today: number;
  pending_human_count: number;
  ai_success_rate: number;
  average_response_time_seconds: number;
  active_conversations_count: number;
  total_products_count: number;
  connected_account_username: string | null;
  is_instagram_connected: boolean;
}

export interface Customer {
  id: string;
  instagram_user_id: string;
  username?: string;
  full_name?: string;
  profile_pic_url?: string;
  preferred_language: string;
}

export interface MessageItem {
  id: string;
  conversation_id: string;
  meta_message_id?: string;
  sender_type: "customer" | "ai" | "human";
  message_type: "text" | "image" | "carousel";
  content?: string;
  media_urls?: string[];
  metadata_json?: Record<string, any>;
  delivery_status: string;
  created_at: string;
}

export interface ConversationItem {
  id: string;
  customer: Customer;
  status: "active" | "pending_human" | "resolved";
  ai_enabled: boolean;
  human_takeover: boolean;
  last_customer_message_at?: string;
  last_message_at: string;
  unread_count: number;
  latest_message?: MessageItem;
  messages?: MessageItem[];
}

export interface ProductItem {
  id: string;
  sku: string;
  name: string;
  category: string;
  description?: string;
  price: number;
  gold_purity?: string;
  gross_weight?: number;
  stock: number;
  status: string;
  tags?: string[];
  images?: { id: string; image_url: string; is_primary: boolean }[];
}

export interface BusinessSettings {
  id: string;
  business_name: string;
  tagline: string;
  default_language: string;
  supported_languages: string[];
  tone: string;
  system_prompt?: string;
  auto_reply_enabled: boolean;
  store_address?: string;
  store_timings: string;
  contact_phone?: string;
  gold_rate_24k_per_10g: number;
  gold_rate_22k_per_10g: number;
  gold_rate_18k_per_10g: number;
}

export interface AITestResult {
  language_detected: string;
  intent_detected: string;
  extracted_entities: Record<string, any>;
  retrieved_products: ProductItem[];
  retrieved_knowledge: any[];
  generated_reply: string;
  fact_validation_passed: boolean;
  validation_flags: string[];
  confidence_score: number;
  processing_time_ms: number;
}

export interface CSVPreviewResult {
  headers: string[];
  sample_rows: Record<string, any>[];
  suggested_mappings: Record<string, string>;
  total_preview_rows: number;
}

export interface CSVImportResult {
  imported_count: number;
  updated_count: number;
  errors: string[];
  total_processed: number;
}

export interface InstagramMediaItem {
  id: string;
  caption?: string;
  media_type: string;
  media_url?: string;
  permalink?: string;
  thumbnail_url?: string;
  timestamp?: string;
  linked_product_ids: string[];
  is_linked: boolean;
  auto_dm_enabled: boolean;
}

export interface PostProductLinkResponse {
  id: string;
  instagram_account_id: string;
  media_id: string;
  media_type: string;
  permalink?: string;
  caption?: string;
  thumbnail_url?: string;
  product_ids: string[];
  products: ProductItem[];
  custom_reply_template?: string;
  auto_dm_enabled: boolean;
  public_reply_enabled: boolean;
  public_reply_text?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProcessedCommentItem {
  id: string;
  comment_id: string;
  media_id: string;
  from_username?: string;
  comment_text: string;
  intent: string;
  private_reply_sent: boolean;
  public_reply_sent: boolean;
  error_message?: string;
  created_at: string;
}


function getAuthHeader(): Record<string, string> {
  return { "X-JewelAI-Request": "1" };
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      credentials: "same-origin",
      cache: "no-store",
      signal: options?.signal ?? AbortSignal.timeout(60000),
      headers: {
        ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...getAuthHeader(),
        ...(options?.headers || {}),
      },
    });
  } catch {
    throw new ApiError(0, "We could not reach the server. Check your connection and try again.");
  }
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    const detail = typeof error.detail === "string" ? error.detail
      : Array.isArray(error.detail) ? error.detail.map((item: { msg: string }) => item.msg).join(" ")
      : "Something went wrong. Please try again.";
    if (res.status === 401 && typeof window !== "undefined" && endpoint !== "/auth/login") {
      window.dispatchEvent(new Event("jewelai:session-expired"));
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  getMe: () => request<User>("/auth/me"),
  getSetup: () => request<{ registration_requires_invite: boolean; instagram_login_available: boolean }>("/auth/setup"),
  login: (email: string, password: string) => request<{ user: User }>("/auth/login", {
    method: "POST", body: JSON.stringify({ email, password }),
  }),
  register: (data: { name: string; email: string; password: string; invite_code?: string }) => request<{ user: User }>("/auth/register", {
    method: "POST", body: JSON.stringify(data),
  }),
  logout: () => request<{ message: string }>("/auth/logout", { method: "POST" }),
  getInstagramStatus: () => request<InstagramStatus>("/auth/instagram/status"),
  startInstagramLogin: () => request<{ url: string; state: string }>("/auth/instagram/login"),
  finishInstagramLogin: (code: string, state: string) => request<{ user: User }>("/auth/instagram/session", {
    method: "POST", body: JSON.stringify({ code, state }),
  }),
  getOverview: () => request<OverviewMetrics>("/analytics/overview"),
  getActivityLogs: () => request<any[]>("/analytics/logs"),
  
  getConversations: (status?: string) =>
    request<ConversationItem[]>(`/conversations${status ? `?status=${status}` : ""}`),
    
  getConversation: (id: string) =>
    request<ConversationItem>(`/conversations/${id}`),
    
  sendHumanReply: (id: string, content: string) =>
    request<MessageItem>(`/conversations/${id}/reply`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
    
  toggleConversationAI: (id: string, ai_enabled?: boolean, human_takeover?: boolean) =>
    request<ConversationItem>(`/conversations/${id}/ai`, {
      method: "PATCH",
      body: JSON.stringify({ ai_enabled, human_takeover }),
    }),
    
  getProducts: (params?: { category?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.category && params.category !== "All") query.set("category", params.category);
    if (params?.search) query.set("search", params.search);
    return request<{ items: ProductItem[]; total: number; categories: string[] }>(`/products?${query.toString()}`);
  },
  
  createProduct: (data: Partial<ProductItem> & { image_urls?: string[] }) =>
    request<ProductItem>("/products", {
      method: "POST",
      body: JSON.stringify(data),
    }),
    
  deleteProduct: (id: string) =>
    request<{ message: string }>(`/products/${id}`, { method: "DELETE" }),
    
  previewCsv: async (file: File): Promise<CSVPreviewResult> => {
    const formData = new FormData();
    formData.append("file", file);
    return request<CSVPreviewResult>("/products/csv-preview", {
      method: "POST",
      body: formData,
    });
  },

  importMappedCsv: async (file: File, mapping: Record<string, string>): Promise<CSVImportResult> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("mapping", JSON.stringify(mapping));
    return request<CSVImportResult>("/products/csv-import-mapped", {
      method: "POST",
      body: formData,
    });
  },

  getKnowledge: () => request<any[]>("/knowledge"),
  createKnowledge: (data: any) =>
    request<any>("/knowledge", {
      method: "POST",
      body: JSON.stringify(data),
    }),
    
  getSettings: () => request<BusinessSettings>("/settings"),
  updateSettings: (data: Partial<BusinessSettings>) =>
    request<BusinessSettings>("/settings", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
    
  testAI: (message: string, image_url?: string, language_override?: string) =>
    request<AITestResult>("/ai/test", {
      method: "POST",
      body: JSON.stringify({ message, image_url, language_override }),
    }),

  getInstagramOAuthUrl: () =>
    request<{ url: string; state: string }>("/auth/instagram/oauth-url"),

  connectInstagram: (code: string, state: string) =>
    request<any>("/auth/instagram/connect", {
      method: "POST",
      body: JSON.stringify({ code, state }),
    }),

  disconnectInstagram: () =>
    request<{ message: string }>("/auth/instagram/disconnect", {
      method: "POST",
    }),

  getPosts: (limit?: number) =>
    request<InstagramMediaItem[]>(`/posts${limit ? `?limit=${limit}` : ""}`),

  getPostLinks: () =>
    request<PostProductLinkResponse[]>("/posts/links"),

  linkPost: (data: {
    media_id: string;
    media_type?: string;
    permalink?: string;
    caption?: string;
    thumbnail_url?: string;
    product_ids: string[];
    custom_reply_template?: string;
    auto_dm_enabled?: boolean;
    public_reply_enabled?: boolean;
    public_reply_text?: string;
  }) =>
    request<PostProductLinkResponse>("/posts/link", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updatePostLink: (link_id: string, data: any) =>
    request<PostProductLinkResponse>(`/posts/link/${link_id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deletePostLink: (link_id: string) =>
    request<{ message: string }>(`/posts/link/${link_id}`, {
      method: "DELETE",
    }),

  getCommentActivity: (limit?: number) =>
    request<ProcessedCommentItem[]>(`/posts/activity${limit ? `?limit=${limit}` : ""}`),
};
