"use client";

import React, { useState, useEffect } from "react";
import {
  BookOpen,
  Plus,
  Coins,
  MapPin,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Trash2,
} from "lucide-react";
import { BusinessSettings, api } from "@/lib/api";

interface KnowledgeViewProps {
  settings: BusinessSettings | null;
  onUpdateSettings: (data: Partial<BusinessSettings>) => Promise<void>;
}

export default function KnowledgeView({ settings, onUpdateSettings }: KnowledgeViewProps) {
  const [faqs, setFaqs] = useState<any[]>([]);
  const [isAddFaqOpen, setIsAddFaqOpen] = useState(false);
  const [newFaq, setNewFaq] = useState({ title: "", content: "", category: "faq" });

  // Gold rates state
  const [gold24k, setGold24k] = useState(settings?.gold_rate_24k_per_10g ? String(settings.gold_rate_24k_per_10g) : "");
  const [gold22k, setGold22k] = useState(settings?.gold_rate_22k_per_10g ? String(settings.gold_rate_22k_per_10g) : "");
  const [gold18k, setGold18k] = useState(settings?.gold_rate_18k_per_10g ? String(settings.gold_rate_18k_per_10g) : "");

  const [timings, setTimings] = useState(settings?.store_timings || "");
  const [address, setAddress] = useState(settings?.store_address || "");
  const [savingRates, setSavingRates] = useState(false);
  const [savingFaq, setSavingFaq] = useState(false);
  const [error, setError] = useState("");

  const loadFaqs = async () => {
    try {
      const data = await api.getKnowledge();
      setFaqs(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load knowledge documents.");
    }
  };

  useEffect(() => {
    loadFaqs();
  }, []);

  const handleSaveRates = async (e: React.FormEvent) => {
    e.preventDefault();
    if (savingRates) return;
    setSavingRates(true);
    try {
      await onUpdateSettings({
        gold_rate_24k_per_10g: gold24k === "" ? 0 : Number(gold24k),
        gold_rate_22k_per_10g: gold22k === "" ? 0 : Number(gold22k),
        gold_rate_18k_per_10g: gold18k === "" ? 0 : Number(gold18k),
        store_timings: timings,
        store_address: address,
      });
      alert("Store details and saved gold rates updated successfully!");
    } catch (err) {
      alert("Failed to save: " + err);
    } finally {
      setSavingRates(false);
    }
  };

  const handleCreateFaq = async (e: React.FormEvent) => {
    e.preventDefault();
    if (savingFaq || !newFaq.title.trim() || !newFaq.content.trim()) return;
    try {
      setSavingFaq(true);
      await api.createKnowledge(newFaq);
      setIsAddFaqOpen(false);
      setNewFaq({ title: "", content: "", category: "faq" });
      loadFaqs();
    } catch (err) {
      alert("Failed to create FAQ: " + err);
    } finally {
      setSavingFaq(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-serif font-bold text-white tracking-wide">
          Knowledge Base, FAQs & Daily Gold Rates
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Add your own business policies, store details, and manually maintained gold rates for AI replies.
        </p>
      </div>

      {error && <p role="alert" className="text-sm text-rose-200">{error}<button onClick={loadFaqs} className="ml-2 underline">Retry knowledge</button></p>}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Gold Rates & Store Hours (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-2xl bg-[#0f1118] border border-[#1e2333] p-5 space-y-4">
            <div className="flex items-center space-x-2">
              <Coins className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Saved Gold Rates (INR per 10g)
              </h3>
            </div>

            <p className="text-xs text-slate-400">Not a live price feed. Keep rates up to date; leave unknown rates empty.</p>
            <form onSubmit={handleSaveRates} className="space-y-3">
              <div>
                <label htmlFor="gold24k" className="text-[11px] text-slate-400 block mb-1">24 Karat</label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-xs text-amber-400 font-bold">₹</span>
                  <input
                    id="gold24k" type="number" min="0" step="any"
                    value={gold24k}
                    onChange={(e) => setGold24k(e.target.value)}
                    className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white font-semibold"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="gold22k" className="text-[11px] text-slate-400 block mb-1">22 Karat</label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-xs text-amber-400 font-bold">₹</span>
                  <input
                    id="gold22k" type="number" min="0" step="any"
                    value={gold22k}
                    onChange={(e) => setGold22k(e.target.value)}
                    className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white font-semibold"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="gold18k" className="text-[11px] text-slate-400 block mb-1">18 Karat</label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-xs text-amber-400 font-bold">₹</span>
                  <input
                    id="gold18k" type="number" min="0" step="any"
                    value={gold18k}
                    onChange={(e) => setGold18k(e.target.value)}
                    className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white font-semibold"
                  />
                </div>
              </div>

              <div className="pt-2 border-t border-[#1e2333]">
                <label className="text-[11px] text-slate-400 block mb-1">Store Timings</label>
                <input
                  type="text"
                  aria-label="Store Timings"
                  value={timings}
                  onChange={(e) => setTimings(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Store Address</label>
                <textarea
                  aria-label="Store Address"
                  rows={2}
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white"
                />
              </div>

              <button
                type="submit"
                disabled={savingRates}
                className="w-full py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 text-xs font-bold transition-all disabled:opacity-50"
              >
                {savingRates ? "Updating..." : "Save Rates & Store Info"}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Policies & FAQs (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-2xl bg-[#0f1118] border border-[#1e2333] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-amber-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Verified Store Knowledge Documents ({faqs.length})
                </h3>
              </div>

              <button
                onClick={() => setIsAddFaqOpen(true)}
                className="px-3 py-1 rounded-xl bg-[#161a26] hover:bg-[#1e2334] border border-[#272e42] text-amber-300 text-xs font-semibold flex items-center space-x-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add FAQ</span>
              </button>
            </div>

            <div className="space-y-3">
              {faqs.map((f) => (
                <div
                  key={f.id}
                  className="p-4 rounded-xl bg-[#141824] border border-[#23283a] space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-100 flex items-center space-x-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                      <span>{f.title}</span>
                    </span>
                    <span className="px-2 py-0.2 rounded text-[10px] uppercase font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      {f.category}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {f.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Add FAQ Modal */}
      {isAddFaqOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="knowledge-title" className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md max-h-[90vh] overflow-y-auto rounded-2xl bg-[#11141e] border border-[#22283a] p-6 space-y-4">
            <h3 id="knowledge-title" className="text-base font-bold text-white font-serif">Add Knowledge Document</h3>
            <form onSubmit={handleCreateFaq} className="space-y-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Category</label>
                <select
                  aria-label="Category"
                  value={newFaq.category}
                  onChange={(e) => setNewFaq({ ...newFaq, category: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                >
                  <option value="faq">FAQ</option>
                  <option value="store_policy">Store Policy / Returns</option>
                  <option value="shipping">Shipping & Delivery</option>
                  <option value="custom_orders">Custom Bespoke Orders</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Title</label>
                <input
                  type="text"
                  aria-label="Title"
                  required
                  placeholder="e.g. Diamond Certification & Warranty"
                  value={newFaq.title}
                  onChange={(e) => setNewFaq({ ...newFaq, title: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Content</label>
                <textarea
                  rows={3}
                  aria-label="Content"
                  required
                  placeholder="Detailed factual policy explanation..."
                  value={newFaq.content}
                  onChange={(e) => setNewFaq({ ...newFaq, content: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  disabled={savingFaq}
                  onClick={() => setIsAddFaqOpen(false)}
                  className="px-3.5 py-1.5 rounded-xl bg-[#1c2130] text-xs text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingFaq}
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 text-xs font-bold"
                >
                  {savingFaq ? "Saving..." : "Save Document"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
