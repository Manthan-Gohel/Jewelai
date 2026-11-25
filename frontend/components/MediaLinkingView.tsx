"use client";

import React, { useState, useEffect } from "react";
import {
  Video,
  Link as LinkIcon,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  MessageSquare,
  Sparkles,
  Search,
  RefreshCw,
  Plus,
  Trash2,
  Send,
  ShieldCheck,
  Tag,
  Clock,
  Layers,
  Check
} from "lucide-react";
import {
  api,
  InstagramMediaItem,
  ProductItem,
  PostProductLinkResponse,
  ProcessedCommentItem
} from "@/lib/api";

export default function MediaLinkingView() {
  const [activeSubTab, setActiveSubTab] = useState<"posts" | "activity">("posts");
  const [posts, setPosts] = useState<InstagramMediaItem[]>([]);
  const [activity, setActivity] = useState<ProcessedCommentItem[]>([]);
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [links, setLinks] = useState<PostProductLinkResponse[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Modal State for Linking
  const [selectedPost, setSelectedPost] = useState<InstagramMediaItem | null>(null);
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [autoDmEnabled, setAutoDmEnabled] = useState(true);
  const [publicReplyEnabled, setPublicReplyEnabled] = useState(true);
  const [publicReplyText, setPublicReplyText] = useState("Sent you a DM with details! ✨");
  const [customReplyTemplate, setCustomReplyTemplate] = useState("");
  const [savingLink, setSavingLink] = useState(false);
  const [productSearch, setProductSearch] = useState("");

  const loadData = async () => {
    try {
      setRefreshing(true);
      setError("");
      const [postsRes, activityRes, productsRes, linksRes] = await Promise.all([
        api.getPosts(25),
        api.getCommentActivity(50),
        api.getProducts(),
        api.getPostLinks(),
      ]);
      setPosts(postsRes || []);
      setActivity(activityRes || []);
      setProducts(productsRes.items || []);
      setLinks(linksRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load posts. Please refresh to try again.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openLinkModal = (post: InstagramMediaItem) => {
    const saved = links.find(link => link.media_id === post.id && link.is_active);
    setSelectedPost(post);
    setSelectedProductIds(post.linked_product_ids || []);
    setAutoDmEnabled(post.auto_dm_enabled ?? true);
    setPublicReplyEnabled(saved?.public_reply_enabled ?? true);
    setPublicReplyText(saved?.public_reply_text ?? "Sent you a DM with details! ✨");
    setCustomReplyTemplate(saved?.custom_reply_template ?? "");
    setProductSearch("");
  };

  const handleSaveLink = async () => {
    if (!selectedPost || savingLink) return;
    setSavingLink(true);
    try {
      const saved = await api.linkPost({
        media_id: selectedPost.id,
        media_type: selectedPost.media_type,
        permalink: selectedPost.permalink,
        caption: selectedPost.caption,
        thumbnail_url: selectedPost.thumbnail_url || selectedPost.media_url,
        product_ids: selectedProductIds,
        custom_reply_template: customReplyTemplate || undefined,
        auto_dm_enabled: autoDmEnabled,
        public_reply_enabled: publicReplyEnabled,
        public_reply_text: publicReplyText,
      });
      setLinks(prev => [...prev.filter(link => link.media_id !== saved.media_id), saved]);

      // Update local state
      setPosts((prev) =>
        prev.map((p) =>
          p.id === selectedPost.id
            ? {
                ...p,
                is_linked: selectedProductIds.length > 0,
                linked_product_ids: selectedProductIds,
                auto_dm_enabled: autoDmEnabled,
              }
            : p
        )
      );
      setSelectedPost(null);
    } catch (err: any) {
      alert("Failed to save post link: " + (err.message || err));
    } finally {
      setSavingLink(false);
    }
  };

  const toggleProductSelection = (id: string) => {
    setSelectedProductIds((prev) =>
      prev.includes(id) ? prev.filter((pId) => pId !== id) : [...prev, id]
    );
  };

  const filteredPosts = posts.filter(
    (p) =>
      !searchQuery ||
      p.caption?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.id.includes(searchQuery)
  );

  const filteredCatalogue = products.filter(
    (prod) =>
      !productSearch ||
      prod.name.toLowerCase().includes(productSearch.toLowerCase()) ||
      prod.sku.toLowerCase().includes(productSearch.toLowerCase()) ||
      prod.category.toLowerCase().includes(productSearch.toLowerCase())
  );

  const recentAutoDMs = activity.filter((a) => a.private_reply_sent).length;

  return (
    <div className="space-y-6">
      {/* Top Banner / Hero */}
      <div className="rounded-2xl border border-[#23283a] bg-gradient-to-r from-[#121622] via-[#0f131c] to-[#141a27] p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
              <span className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
                <Video className="w-5 h-5" />
              </span>
              <h1 className="text-xl font-serif font-bold text-slate-100 tracking-wide">
                Video Post → Comments → Auto DM
              </h1>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Meta Private Reply API
              </span>
            </div>
            <p className="text-sm text-slate-400 max-w-2xl">
              Tag your Instagram Reels & Posts with catalogue SKUs. Eligible comments can receive catalogue-grounded private replies when global and post-level automation are enabled.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="px-4 py-2 rounded-xl bg-[#171b28] border border-[#262c3f] text-right">
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                Recent Private Replies
              </div>
              <div className="text-lg font-bold text-amber-300">
                {recentAutoDMs} <span className="text-xs text-slate-500 font-normal">in loaded activity</span>
              </div>
            </div>

            <button
              onClick={loadData}
              disabled={refreshing}
              className="p-2.5 rounded-xl border border-[#262c3f] bg-[#161a26] hover:bg-[#1f2536] text-slate-300 transition-colors"
              title="Refresh Posts & Comments"
              aria-label="Refresh Posts & Comments"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-amber-400" : ""}`} />
            </button>
          </div>
        </div>

        {/* Sub-tab Navigation */}
        <div className="flex items-center space-x-2 mt-6 border-t border-[#1d2232] pt-4">
          <button
            onClick={() => setActiveSubTab("posts")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-2 ${
              activeSubTab === "posts"
                ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Recent Reels & Posts ({posts.length})</span>
          </button>
          <button
            onClick={() => setActiveSubTab("activity")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-2 ${
              activeSubTab === "activity"
                ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Auto-DM Activity Feed ({activity.length})</span>
          </button>
        </div>
      </div>

      {error && <p role="alert" className="rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error} Use Refresh Posts & Comments to retry.</p>}
      <p className="text-xs text-slate-400">Post switches do not override the global AI pause. Delivery is subject to provider permissions, policy and the server-configured daily cap.</p>

      {/* Main Content Area */}
      {activeSubTab === "posts" && (
        <div className="space-y-4">
          {/* Search bar */}
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                placeholder="Search caption or post ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#121622] border border-[#23283a] rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50"
              />
            </div>
            <div className="text-xs text-slate-400">
              Showing <span className="text-amber-300 font-semibold">{filteredPosts.length}</span> published media items
            </div>
          </div>

          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-400" />
              Loading posts from connected Instagram account...
            </div>
          ) : filteredPosts.length === 0 ? (
            <div className="p-12 text-center rounded-2xl border border-dashed border-[#23283a] bg-[#0f121a] text-slate-400">
              <Video className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              <p className="text-sm font-medium">No Instagram media items found</p>
              <p className="text-xs text-slate-500 mt-1">
                Ensure your Instagram account is connected under Meta Integration and has published Reels or Posts.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredPosts.map((post) => {
                const linkedCount = post.linked_product_ids?.length || 0;
                return (
                  <div
                    key={post.id}
                    className={`rounded-xl border transition-all overflow-hidden flex flex-col ${
                      post.is_linked
                        ? "border-amber-500/30 bg-[#121622]/90 shadow-lg shadow-amber-500/5"
                        : "border-[#1f2434] bg-[#0e111a]"
                    }`}
                  >
                    {/* Media Header / Thumbnail */}
                    <div className="relative h-48 bg-[#090b10] flex items-center justify-center overflow-hidden">
                      {post.thumbnail_url ? (
                        <img
                          src={post.thumbnail_url}
                          alt="Instagram Post"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <Video className="w-12 h-12 text-slate-600" />
                      )}

                      <div className="absolute top-2 left-2 flex items-center space-x-1.5">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-black/70 backdrop-blur-md text-slate-200 border border-white/10">
                          {post.media_type}
                        </span>
                        {post.is_linked && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/90 text-black font-mono">
                            {linkedCount} SKU{linkedCount > 1 ? "s" : ""} Linked
                          </span>
                        )}
                      </div>

                      {post.permalink && (
                        <a
                          href={post.permalink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 text-slate-200 transition-colors"
                          title="View on Instagram"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>

                    {/* Caption & Metadata */}
                    <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                      <div>
                        <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                          {post.caption || "No caption provided"}
                        </p>
                        {post.timestamp && (
                          <div className="flex items-center space-x-1 text-[11px] text-slate-500 mt-2">
                            <Clock className="w-3 h-3" />
                            <span>{new Date(post.timestamp).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>

                      <div className="pt-3 border-t border-[#1f2434] flex items-center justify-between">
                        <div className="flex items-center space-x-1 text-xs">
                          {post.is_linked ? (
                            <span className="flex items-center text-emerald-400 space-x-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span className="text-[11px] font-medium">{post.auto_dm_enabled ? "Auto-DM configured" : "Auto-DM paused"}</span>
                            </span>
                          ) : (
                            <span className="text-slate-500 text-[11px]">Unlinked</span>
                          )}
                        </div>

                        <button
                          onClick={() => openLinkModal(post)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5 ${
                            post.is_linked
                              ? "bg-[#1d2334] hover:bg-[#262e45] text-amber-300 border border-amber-500/30"
                              : "bg-amber-500 hover:bg-amber-400 text-black font-semibold shadow-md shadow-amber-500/20"
                          }`}
                        >
                          <LinkIcon className="w-3.5 h-3.5" />
                          <span>{post.is_linked ? "Manage Link" : "Link Products"}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Activity Feed SubTab */}
      {activeSubTab === "activity" && (
        <div className="rounded-xl border border-[#1f2434] bg-[#0f121a] overflow-hidden">
          <div className="p-4 border-b border-[#1f2434] flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200">
              Live Comment-to-DM Execution Log
            </h2>
            <span className="text-xs text-slate-500">
              Showing last {activity.length} comment events
            </span>
          </div>

          {activity.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No comment events recorded yet. When customers comment on linked reels, events appear here instantly.
            </div>
          ) : (
            <div className="divide-y divide-[#181d2a]">
              {activity.map((act) => (
                <div key={act.id} className="p-4 flex items-start justify-between gap-4 text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-200">
                        @{act.from_username || "instagram_user"}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-[#191f2e] text-amber-300 border border-[#273047]">
                        {act.intent}
                      </span>
                      <span className="text-slate-500 text-[11px]">
                        {new Date(act.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-slate-300 bg-[#141824] px-3 py-1.5 rounded-lg border border-[#202738] italic">
                      "{act.comment_text}"
                    </p>
                    {act.error_message && (
                      <p className="text-rose-400 text-[11px] flex items-center space-x-1">
                        <AlertCircle className="w-3 h-3" />
                        <span>{act.error_message}</span>
                      </p>
                    )}
                  </div>

                  <div className="flex flex-col items-end space-y-1 shrink-0">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold flex items-center space-x-1 ${
                        act.private_reply_sent
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      <Send className="w-3 h-3" />
                      <span>{act.private_reply_sent ? "Private DM Sent" : "No DM"}</span>
                    </span>
                    {act.public_reply_sent && (
                      <span className="text-[10px] text-amber-400">Public reply posted</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Linking Modal */}
      {selectedPost && (
        <div role="dialog" aria-modal="true" aria-labelledby="post-link-title" className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#10141f] border border-[#252c40] rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-6">
            <div className="flex items-start justify-between border-b border-[#1f2538] pb-4">
              <div>
                <h3 id="post-link-title" className="text-lg font-serif font-bold text-slate-100 flex items-center space-x-2">
                  <Tag className="w-5 h-5 text-amber-400" />
                  <span>Link Jewellery Catalogue to Post</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Post ID: <span className="font-mono text-amber-300">{selectedPost.id}</span>
                </p>
              </div>
              <button
                aria-label="Close post link"
                disabled={savingLink}
                onClick={() => setSelectedPost(null)}
                className="text-slate-500 hover:text-slate-300 text-sm font-semibold p-1"
              >
                ✕
              </button>
            </div>

            {/* Post Snippet */}
            <div className="flex items-center space-x-3 p-3 rounded-xl bg-[#0a0d14] border border-[#1b2130]">
              {selectedPost.thumbnail_url && (
                <img
                  src={selectedPost.thumbnail_url}
                  alt="Post"
                  className="w-14 h-14 rounded-lg object-cover"
                />
              )}
              <div className="text-xs text-slate-300 flex-1 line-clamp-2">
                {selectedPost.caption || "No caption"}
              </div>
            </div>

            {/* Product Selector */}
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <label className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                  Select Catalogue Jewellery Items ({selectedProductIds.length} selected)
                </label>
                <div className="relative w-64">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Filter products..."
                    value={productSearch}
                    onChange={(e) => setProductSearch(e.target.value)}
                    className="w-full bg-[#151a27] border border-[#262d40] rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50"
                  />
                </div>
              </div>

              <div className="max-h-56 overflow-y-auto rounded-xl border border-[#1f2538] bg-[#0c0f17] divide-y divide-[#181d2a]">
                {filteredCatalogue.length === 0 ? (
                  <div className="p-6 text-center text-slate-500 text-xs">
                    No matching products in catalogue.
                  </div>
                ) : (
                  filteredCatalogue.map((prod) => {
                    const isSelected = selectedProductIds.includes(prod.id);
                    return (
                      <label
                        key={prod.id}
                        className={`p-3 flex items-center justify-between cursor-pointer transition-colors ${
                          isSelected ? "bg-amber-500/10" : "hover:bg-[#141926]"
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <input type="checkbox" aria-label={prod.name} checked={isSelected} onChange={() => toggleProductSelection(prod.id)} className="w-5 h-5 accent-amber-400 shrink-0" />
                          <div>
                            <div className="text-xs font-semibold text-slate-200">
                              {prod.name}
                            </div>
                            <div className="text-[11px] text-slate-400">
                              SKU: {prod.sku} • {prod.gold_purity || "Pure Gold"} • ₹{prod.price.toLocaleString("en-IN")}
                            </div>
                          </div>
                        </div>
                        <span className="text-xs font-semibold text-amber-300">
                          ₹{prod.price.toLocaleString("en-IN")}
                        </span>
                      </label>
                    );
                  })
                )}
              </div>
            </div>

            {/* Automation Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="p-3.5 rounded-xl border border-[#1f2538] bg-[#0e121c] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">Auto-DM on Comment</span>
                  <input
                    type="checkbox"
                    aria-label="Auto-DM on Comment"
                    checked={autoDmEnabled}
                    onChange={(e) => setAutoDmEnabled(e.target.checked)}
                    className="w-4 h-4 accent-amber-500 rounded cursor-pointer"
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Sends an official Meta Private Reply DM to anyone asking about price or details.
                </p>
              </div>

              <div className="p-3.5 rounded-xl border border-[#1f2538] bg-[#0e121c] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">Public Reply</span>
                  <input
                    type="checkbox"
                    aria-label="Public Reply"
                    checked={publicReplyEnabled}
                    onChange={(e) => setPublicReplyEnabled(e.target.checked)}
                    className="w-4 h-4 accent-amber-500 rounded cursor-pointer"
                  />
                </div>
                <input
                  type="text"
                  aria-label="Public reply text"
                  value={publicReplyText}
                  onChange={(e) => setPublicReplyText(e.target.value)}
                  placeholder="e.g. Sent you a DM with details! ✨"
                  className="w-full bg-[#151a27] border border-[#262d40] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>
            </div>

            {/* Custom Reply Template (Optional) */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Custom Reply Template (Optional)
              </label>
              <textarea
                rows={3}
                aria-label="Custom Reply Template (Optional)"
                value={customReplyTemplate}
                onChange={(e) => setCustomReplyTemplate(e.target.value)}
                placeholder="Leave blank for automatic luxury AI formatting. Tags supported: {product_name}, {price}, {purity}, {sku}"
                className="w-full bg-[#121622] border border-[#23283a] rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-[#1f2538]">
              <button
                onClick={() => setSelectedPost(null)}
                disabled={savingLink}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveLink}
                disabled={savingLink}
                className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-amber-500 hover:bg-amber-400 text-black shadow-lg shadow-amber-500/20 transition-all flex items-center space-x-2"
              >
                {savingLink ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Save Link</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
