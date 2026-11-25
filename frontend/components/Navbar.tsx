"use client";

import React from "react";
import { Sparkles, Instagram, Zap } from "lucide-react";
import { BusinessSettings } from "@/lib/api";

interface NavbarProps {
  settings: BusinessSettings | null;
  isConnected: boolean;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onToggleAutoReply: () => void;
}

export default function Navbar({
  settings,
  isConnected,
  activeTab,
  setActiveTab,
  onToggleAutoReply,
}: NavbarProps) {
  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "inbox", label: "Live Inbox" },
    { id: "catalogue", label: "Catalogue" },
    { id: "posts", label: "Reels & Post Linking" },
    { id: "playground", label: "AI Playground" },
    { id: "knowledge", label: "Knowledge & FAQs" },
    { id: "instagram", label: "Meta Integration" },
    { id: "settings", label: "Settings & Logs" },
  ];

  return (
    <header className="border-b border-[#1f2433] bg-[#0c0e14]/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400/20 via-gold-400 to-amber-600 flex items-center justify-center p-0.5 shadow-lg shadow-gold-500/20">
              <div className="w-full h-full bg-[#0d0f17] rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-serif text-lg tracking-wider font-bold gold-gradient-text">
                  JEWELAI
                </span>
                <span className="px-1.5 py-0.5 text-[10px] font-semibold tracking-wider rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  INSTAGRAM
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                {settings?.business_name || "Your workspace"}
              </p>
            </div>
          </div>

          {/* Gold Rates & Status Badge */}
          <div className="hidden md:flex items-center space-x-4">
            {settings && <div className="px-3 py-1.5 rounded-lg bg-[#141824] border border-[#23283a] flex items-center space-x-3 text-xs">
              <div className="flex items-center space-x-1.5 text-amber-300">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="font-medium">Saved 22K Rate:</span>
              </div>
              <span className="text-slate-200 font-semibold">
                {settings.gold_rate_22k_per_10g > 0 ? `₹${settings.gold_rate_22k_per_10g.toLocaleString("en-IN")} / 10g` : "Not set"}
              </span>
            </div>}

            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#141824] border border-[#23283a] text-xs">
              <Instagram className="w-3.5 h-3.5 text-pink-400" />
              <span className="text-slate-300">{isConnected ? "Instagram connected" : "Not connected"}</span>
              <span className={`inline-block w-2 h-2 rounded-full ${isConnected ? "bg-emerald-400" : "bg-slate-500"}`} />
            </div>

            {/* AI Toggle */}
            <button
              onClick={onToggleAutoReply}
              disabled={!isConnected || !settings}
              aria-pressed={isConnected && !!settings?.auto_reply_enabled}
              className={`flex min-h-11 items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors disabled:opacity-50 ${
                isConnected && settings?.auto_reply_enabled
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                  : "bg-rose-500/10 border-rose-500/30 text-rose-400 hover:bg-rose-500/20"
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{isConnected && settings?.auto_reply_enabled ? "AI Auto-Reply Active" : "AI Paused"}</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 overflow-x-auto pb-1 scrollbar-none">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3.5 py-2 text-xs font-medium rounded-t-lg transition-all border-b-2 whitespace-nowrap ${
                  isActive
                    ? "border-amber-400 text-amber-300 bg-[#161a26]/80 font-semibold"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-[#121520]/50"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
