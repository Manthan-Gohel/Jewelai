"use client";

import React, { useState, useEffect } from "react";
import {
  MessageSquare,
  Search,
  Bot,
  UserCheck,
  Send,
  Sparkles,
  ShieldAlert,
  Clock,
  Instagram,
  CheckCircle2,
  RefreshCw,
  Image as ImageIcon,
  ExternalLink,
} from "lucide-react";
import { ConversationItem, MessageItem, api } from "@/lib/api";
import { formatTime, formatDate, formatCurrency } from "@/lib/utils";

export default function InboxView() {
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeConversation, setActiveConversation] = useState<ConversationItem | null>(null);
  const [filter, setFilter] = useState<"all" | "pending_human" | "active">("all");
  const [search, setSearch] = useState("");
  const [replyText, setReplyText] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  // Load conversations
  const loadConversations = async () => {
    try {
      setLoading(true);
      const data = await api.getConversations();
      setConversations(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load conversations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
    const interval = setInterval(loadConversations, 10000);
    return () => clearInterval(interval);
  }, []);

  // Load active conversation details when selection changes
  useEffect(() => {
    if (!selectedId) return;
    const fetchDetail = async () => {
      try {
        const detail = await api.getConversation(selectedId);
        setActiveConversation(detail);
      } catch (err) {
        console.error("Failed to load conversation detail:", err);
      }
    };
    fetchDetail();
  }, [selectedId]);

  // Handle staff manual reply
  const handleSendReply = async () => {
    if (!selectedId || !replyText.trim() || sending) return;
    try {
      setSending(true);
      await api.sendHumanReply(selectedId, replyText.trim());
      setReplyText("");
      // Refresh detail
      const detail = await api.getConversation(selectedId);
      setActiveConversation(detail);
      loadConversations();
    } catch (err) {
      alert("Failed to send reply: " + err);
    } finally {
      setSending(false);
    }
  };

  // Toggle Human Takeover / Resume AI
  const handleToggleTakeover = async () => {
    if (!activeConversation) return;
    const newTakeover = !activeConversation.human_takeover;
    try {
      const updated = await api.toggleConversationAI(
        activeConversation.id,
        !newTakeover,
        newTakeover
      );
      setActiveConversation(updated);
      loadConversations();
    } catch (err) {
      alert("Failed to update status: " + err);
    }
  };

  const filteredConversations = conversations.filter((c) => {
    if (filter === "pending_human" && !c.human_takeover) return false;
    if (filter === "active" && c.human_takeover) return false;
    if (search) {
      const q = search.toLowerCase();
      const matchName = c.customer.full_name?.toLowerCase().includes(q);
      const matchUser = c.customer.username?.toLowerCase().includes(q);
      return matchName || matchUser;
    }
    return true;
  });

  return (
    <div className="h-[calc(100vh-140px)] rounded-2xl bg-[#0f1118] border border-[#1e2333] overflow-hidden flex flex-col md:flex-row">
      {/* Left Pane: Conversation Threads */}
      <div className="w-full md:w-80 lg:w-96 border-b md:border-b-0 md:border-r border-[#1e2333] flex flex-col bg-[#0c0e15]">
        {/* Search & Filter Header */}
        <div className="p-3 border-b border-[#1e2333] space-y-2">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search customers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-400"
            />
          </div>

          <div className="flex space-x-1">
            {[
              { id: "all", label: "All" },
              { id: "pending_human", label: "Needs Staff" },
              { id: "active", label: "AI Handled" },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id as any)}
                className={`flex-1 py-1 text-[11px] font-medium rounded-lg transition-colors ${
                  filter === f.id
                    ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#141824]"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto divide-y divide-[#1a1e2c]">
          {filteredConversations.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              {loading ? "Loading conversations..." : "No conversations found."}
            </div>
          ) : (
            filteredConversations.map((conv) => {
              const isSelected = selectedId === conv.id;
              return (
                <div
                  key={conv.id}
                  onClick={() => setSelectedId(conv.id)}
                  className={`p-3 cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-[#181d2a] border-l-2 border-amber-400"
                      : "hover:bg-[#121622]"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-500/30 to-purple-500/30 border border-[#2d3448] flex items-center justify-center font-bold text-xs text-slate-200 shrink-0">
                        {conv.customer.username?.[0]?.toUpperCase() || "C"}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center space-x-1.5">
                          <span className="text-xs font-semibold text-slate-200 truncate">
                            @{conv.customer.username || `user_${conv.customer.instagram_user_id.slice(-4)}`}
                          </span>
                          {conv.human_takeover ? (
                            <span className="px-1.5 py-0.2 rounded text-[9px] bg-purple-500/15 text-purple-300 border border-purple-500/30 font-medium">
                              Staff Takeover
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.2 rounded text-[9px] bg-amber-500/15 text-amber-300 border border-amber-500/30 font-medium flex items-center space-x-1">
                              <Sparkles className="w-2.5 h-2.5" />
                              <span>AI</span>
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 truncate mt-0.5">
                          {conv.latest_message?.content || "Sent reference attachment"}
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] text-slate-500 whitespace-nowrap">
                      {formatTime(conv.last_message_at)}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Pane: Active Thread */}
      {activeConversation ? (
        <div className="flex-1 flex flex-col bg-[#0f1118]">
          {/* Thread Header */}
          <div className="p-3.5 border-b border-[#1e2333] flex items-center justify-between bg-[#11141e]">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-full bg-amber-500/20 border border-amber-500/30 flex items-center justify-center font-bold text-sm text-amber-300">
                {activeConversation.customer.username?.[0]?.toUpperCase() || "C"}
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-xs font-bold text-white">
                    @{activeConversation.customer.username || "Customer"}
                  </h3>
                  <span className="text-[11px] text-slate-400">
                    (ID: {activeConversation.customer.instagram_user_id})
                  </span>
                </div>
                <div className="flex items-center space-x-3 text-[11px] text-slate-400 mt-0.5">
                  <span className="flex items-center space-x-1 text-emerald-400">
                    <Clock className="w-3 h-3" />
                    <span>24h Messaging Window Active</span>
                  </span>
                  <span>•</span>
                  <span>Lang: {activeConversation.customer.preferred_language.toUpperCase()}</span>
                </div>
              </div>
            </div>

            {/* Takeover Control */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleToggleTakeover}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 border transition-all ${
                  activeConversation.human_takeover
                    ? "bg-amber-500/15 border-amber-500/30 text-amber-300 hover:bg-amber-500/25"
                    : "bg-purple-500/15 border-purple-500/30 text-purple-300 hover:bg-purple-500/25"
                }`}
              >
                {activeConversation.human_takeover ? (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Resume AI Replies</span>
                  </>
                ) : (
                  <>
                    <UserCheck className="w-3.5 h-3.5" />
                    <span>Take Over Thread</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Message History */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {activeConversation.messages?.map((msg) => {
              const isCustomer = msg.sender_type === "customer";
              const isAI = msg.sender_type === "ai";

              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isCustomer ? "items-start" : "items-end"}`}
                >
                  <div className="flex items-center space-x-1.5 mb-1 px-1">
                    {isCustomer ? (
                      <span className="text-[10px] text-slate-400 font-medium">Customer</span>
                    ) : isAI ? (
                      <span className="text-[10px] text-amber-400 font-semibold flex items-center space-x-1">
                        <Sparkles className="w-2.5 h-2.5" />
                        <span>AI Assistant</span>
                      </span>
                    ) : (
                      <span className="text-[10px] text-purple-400 font-semibold flex items-center space-x-1">
                        <UserCheck className="w-2.5 h-2.5" />
                        <span>Staff Member</span>
                      </span>
                    )}
                    <span className="text-[10px] text-slate-500">
                      {formatTime(msg.created_at)}
                    </span>
                  </div>

                  <div
                    className={`max-w-md rounded-2xl p-3.5 text-xs leading-relaxed ${
                      isCustomer
                        ? "bg-[#181c28] border border-[#272e42] text-slate-100 rounded-tl-sm"
                        : isAI
                        ? "bg-gradient-to-br from-[#1d2230] to-[#171b26] border border-amber-500/25 text-amber-50 rounded-tr-sm shadow-lg shadow-amber-950/20"
                        : "bg-purple-950/40 border border-purple-500/30 text-purple-50 rounded-tr-sm"
                    }`}
                  >
                    {/* Customer attached photo preview */}
                    {msg.media_urls && msg.media_urls.length > 0 && (
                      <div className="mb-2 rounded-xl overflow-hidden border border-[#2d354a]">
                        <img
                          src={msg.media_urls[0]}
                          alt="Customer jewellery reference"
                          className="w-full max-h-48 object-cover"
                        />
                        <div className="p-1.5 bg-[#121520] text-[10px] text-amber-300 flex items-center space-x-1">
                          <ImageIcon className="w-3 h-3" />
                          <span>Customer reference photo</span>
                        </div>
                      </div>
                    )}

                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Reply Box */}
          <div className="p-3 border-t border-[#1e2333] bg-[#11141e]">
            {activeConversation.human_takeover && (
              <div className="mb-2 px-3 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-[11px] text-purple-300 flex items-center space-x-2">
                <UserCheck className="w-3 h-3" />
                <span>Human takeover is active. Automated AI replies are paused for this customer.</span>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <input
                type="text"
                placeholder={
                  activeConversation.human_takeover
                    ? "Type manual reply as jewellery staff..."
                    : "Replying manually will automatically engage Human Takeover..."
                }
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendReply()}
                className="flex-1 px-3.5 py-2.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
              />
              <button
                onClick={handleSendReply}
                disabled={sending || !replyText.trim()}
                className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs flex items-center space-x-1.5 disabled:opacity-50 transition-all shrink-0"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-xs text-slate-500">
          Select a customer conversation to view history
        </div>
      )}
    </div>
  );
}
