"use client";

import React from "react";
import {
  MessageSquare,
  Bot,
  UserCheck,
  Award,
  Zap,
  Gem,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Shield,
  Layers,
} from "lucide-react";
import { OverviewMetrics, BusinessSettings } from "@/lib/api";

interface OverviewViewProps {
  metrics: OverviewMetrics | null;
  settings: BusinessSettings | null;
  onNavigate: (tab: string) => void;
}

export default function OverviewView({
  metrics,
  settings,
  onNavigate,
}: OverviewViewProps) {
  const cards = [
    {
      title: "Messages (24 hours)",
      value: metrics?.total_messages_today ?? "—",
      subtext: "Customer and staff messages",
      icon: MessageSquare,
      color: "from-blue-500/20 to-indigo-500/10 text-blue-400 border-blue-500/20",
    },
    {
      title: "AI Responses Sent",
      value: metrics?.ai_replies_today ?? "—",
      subtext: "In the last 24 hours",
      icon: Bot,
      color: "from-amber-500/20 to-gold-500/10 text-amber-400 border-amber-500/20",
    },
    {
      title: "Staff Takeover Required",
      value: metrics?.pending_human_count ?? "—",
      subtext: "Complaints & negotiations",
      icon: UserCheck,
      color: "from-purple-500/20 to-pink-500/10 text-purple-400 border-purple-500/20",
    },
    {
      title: "Validation Pass Rate",
      value: metrics ? `${metrics.ai_success_rate}%` : "—",
      subtext: "Checks passed / replies checked",
      icon: Award,
      color: "from-emerald-500/20 to-teal-500/10 text-emerald-400 border-emerald-500/20",
    },
    {
      title: "Avg Response Time",
      value: metrics ? `${metrics.average_response_time_seconds}s` : "—",
      subtext: "AI processing, last 24 hours",
      icon: Zap,
      color: "from-yellow-500/20 to-amber-500/10 text-yellow-400 border-yellow-500/20",
    },
    {
      title: "Live Catalogue Items",
      value: metrics?.total_products_count ?? "—",
      subtext: "Verified stock & purity",
      icon: Gem,
      color: "from-rose-500/20 to-amber-500/10 text-rose-400 border-rose-500/20",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-2xl gold-card p-6 md:p-8">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium mb-3">
            <Shield className="w-3.5 h-3.5" />
            <span>Official Meta Instagram Messaging Integration</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-serif font-bold text-white tracking-wide">
            Intelligent Instagram DM Assistant
          </h1>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed">
            Real-time automated customer engagement for luxury fine jewellery.
            Understands English, Hindi, and Gujarati, analyzes customer reference photos, and quotes only verified catalogue prices and BIS hallmarked purities.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate("inbox")}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-semibold text-xs tracking-wide shadow-lg shadow-amber-500/20 flex items-center space-x-2 transition-all"
            >
              <span>Open Live Inbox</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate("playground")}
              className="px-4 py-2 rounded-xl bg-[#1a1f2e] hover:bg-[#22283a] text-slate-200 border border-[#2b3247] font-medium text-xs flex items-center space-x-2 transition-all"
            >
              <Bot className="w-4 h-4 text-amber-400" />
              <span>Simulate AI Playground</span>
            </button>
          </div>
        </div>

        {/* Decorative background glow */}
        <div className="absolute right-0 top-0 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div
              key={i}
              className="p-4 rounded-xl bg-[#11141d] border border-[#1e2333] hover:border-amber-500/30 transition-all flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400 font-medium truncate">
                  {c.title}
                </span>
                <div
                  className={`w-7 h-7 rounded-lg bg-gradient-to-br ${c.color} border flex items-center justify-center`}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-xl font-bold text-white tracking-tight">
                  {c.value}
                </div>
                <div className="text-[11px] text-slate-400 mt-1 truncate">
                  {c.subtext}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Two Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Compliance & Policy Checklist */}
        <div className="lg:col-span-2 rounded-2xl bg-[#11141d] border border-[#1e2333] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-semibold text-white">
                Meta Compliance & Production Safeguards
              </h2>
            </div>
            <span className="px-2 py-0.5 rounded text-[11px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              Built-in safeguards
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {[
              {
                title: "24-Hour Messaging Window",
                desc: "Automated responses strictly suppressed if customer inquiry is > 24 hours old.",
                status: "Enforced",
              },
              {
                title: "Catalogue Fact Checks",
                desc: "AI responses verified against database prices and purity before dispatch.",
                status: "Active",
              },
              {
                title: "Human Takeover Gate",
                desc: "Staff takeover immediately halts background AI replies for that customer thread.",
                status: "Protected",
              },
              {
                title: "HMAC-SHA256 Webhooks",
                desc: "Every incoming Meta payload verified with X-Hub-Signature-256.",
                status: "Verified",
              },
              {
                title: "Duplicate Event Prevention",
                desc: "Meta message IDs deduplicated at database and worker layers.",
                status: "Protected",
              },
              {
                title: "Token Encryption at Rest",
                desc: "Instagram authorization tokens encrypted at rest with Fernet.",
                status: "Encrypted",
              },
            ].map((item, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-[#151926]/60 border border-[#23283c] flex items-start space-x-3"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-slate-200">
                      {item.title}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Multilingual & Brand Intelligence */}
        <div className="rounded-2xl bg-[#11141d] border border-[#1e2333] p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Layers className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-semibold text-white">
                Multilingual AI Coverage
              </h2>
            </div>

            <div className="space-y-3">
              {[
                {
                  lang: "English (en)",
                  sample: "Do you have gold earrings under ₹15,000?",
                  color: "bg-blue-400",
                },
                {
                  lang: "Hindi (hi / Hinglish)",
                  sample: "Kya aapke paas 22k gold necklace hai?",
                  color: "bg-amber-400",
                },
                {
                  lang: "Gujarati (gu / Gujlish)",
                  sample: "Mare 20 hajar ma gold ring joiye",
                  color: "bg-emerald-400",
                },
              ].map((l, i) => (
                <div key={i} className="p-3 rounded-xl bg-[#151926]/50 border border-[#202538]">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-200">{l.lang}</span>
                    <span className="text-amber-400 font-bold">Supported</span>
                  </div>
                  <p className="text-[10px] text-slate-400 italic">"{l.sample}"</p>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-[#1e2333] flex items-center justify-between text-xs">
            <span className="text-slate-400">Current AI Persona:</span>
            <span className="font-semibold text-amber-300 capitalize">{settings?.tone || "Not configured"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
