"use client";

import React, { useState } from "react";
import {
  Bot,
  Sparkles,
  Send,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
  Globe,
  Tag,
  Image as ImageIcon,
  Flame,
  ArrowRight,
} from "lucide-react";
import { AITestResult, api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export default function PlaygroundView() {
  const [message, setMessage] = useState("Do you have gold earrings under ₹15,000?");
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AITestResult | null>(null);
  const [error, setError] = useState("");

  const sampleScenarios = [
    {
      title: "English Enquiry",
      lang: "EN",
      text: "Do you have gold earrings under ₹15,000?",
      img: "",
    },
    {
      title: "Gujarati Enquiry",
      lang: "GU",
      text: "Mare 20 hajar ma gold ring joiye",
      img: "",
    },
    {
      title: "Hindi Enquiry",
      lang: "HI",
      text: "Kya aapke paas 22k gold necklace hai?",
      img: "",
    },
    {
      title: "Customer Photo Match",
      lang: "EN",
      text: "Do you have something like this ring in 22K?",
      img: "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=600&q=80",
    },
    {
      title: "Human Takeover Trigger",
      lang: "EN",
      text: "Can I speak to a human manager for special discount?",
      img: "",
    },
  ];

  const handleRunSimulation = async (textToRun = message, imgToRun = imageUrl) => {
    if (loading || (!textToRun.trim() && !imgToRun)) return;
    try {
      setLoading(true);
      setError("");
      setResult(null);
      const res = await api.testAI(textToRun, imgToRun || undefined);
      setResult(res);
    } catch (err: any) {
      setError("Simulation failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-serif font-bold text-white tracking-wide">
          AI Testing & Grounding Playground
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Interactive simulator to test natural language understanding, customer reference photos, catalogue grounding, and anti-hallucination validation before deploying live.
        </p>
      </div>

      {/* Quick Scenarios Bar */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
        <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider shrink-0 mr-1">
          Quick Tests:
        </span>
        {sampleScenarios.map((s, idx) => (
          <button
            key={idx}
            disabled={loading}
            onClick={() => {
              setMessage(s.text);
              setImageUrl(s.img);
              handleRunSimulation(s.text, s.img);
            }}
            className="px-3 py-1.5 rounded-xl bg-[#131622] hover:bg-[#1a2030] text-slate-300 border border-[#23293c] text-xs whitespace-nowrap flex items-center space-x-1.5 transition-all"
          >
            <span className="px-1 py-0.2 rounded text-[9px] bg-amber-500/20 text-amber-300 font-bold">
              {s.lang}
            </span>
            <span>{s.title}</span>
          </button>
        ))}
      </div>

      {/* Two Column Simulator Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Input Form (5 cols) */}
        <div className="lg:col-span-5 rounded-2xl bg-[#0f1118] border border-[#1e2333] p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Customer Message (Instagram DM)
              </label>
              <textarea
                aria-label="Customer Message (Instagram DM)"
                rows={4}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type customer question in English, Hindi, or Gujarati..."
                className="w-full p-3 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400 leading-relaxed"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Customer Reference Photo URL (Optional)
              </label>
              <div className="relative">
                <ImageIcon className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
                <input
                  type="url"
                  aria-label="Customer Reference Photo URL (Optional)"
                  placeholder="https://images.unsplash.com/..."
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                />
              </div>
              {imageUrl && (
                <div className="mt-2 h-28 rounded-xl overflow-hidden border border-[#23283a]">
                  <img src={imageUrl} alt="Reference Preview" className="w-full h-full object-cover" />
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => handleRunSimulation()}
            disabled={loading || (!message.trim() && !imageUrl)}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-amber-500/20 transition-all disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>{loading ? "Synthesizing Grounded Reply..." : "Simulate AI Execution"}</span>
          </button>
        </div>

        {/* Right Column: Grounded Result Breakdown (7 cols) */}
        <div className="lg:col-span-7 rounded-2xl bg-[#0f1118] border border-[#1e2333] p-5 space-y-4">
          {error && <p role="alert" className="text-sm text-rose-200">{error} Try the simulation again.</p>}
          {result ? (
            <div className="space-y-4">
              {/* Intent & Entity Pill Bar */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <div className="px-2.5 py-1 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-400 flex items-center space-x-1.5">
                  <Globe className="w-3.5 h-3.5" />
                  <span>Language: <strong className="uppercase">{result.language_detected}</strong></span>
                </div>

                <div className="px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5" />
                  <span>Intent: <strong className="capitalize">{result.intent_detected.replace("_", " ")}</strong></span>
                </div>

                {result.extracted_entities.category && (
                  <div className="px-2.5 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-xs text-purple-300">
                    Category: <strong>{result.extracted_entities.category}</strong>
                  </div>
                )}

                {result.extracted_entities.budget_max && (
                  <div className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
                    Budget Max: <strong>{formatCurrency(result.extracted_entities.budget_max)}</strong>
                  </div>
                )}

                {result.extracted_entities.purity && (
                  <div className="px-2.5 py-1 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-xs text-yellow-300">
                    Purity: <strong>{result.extracted_entities.purity}</strong>
                  </div>
                )}

                <div className="px-2.5 py-1 rounded-lg bg-slate-800 text-[11px] text-slate-300 ml-auto flex items-center space-x-1">
                  <Clock className="w-3 h-3 text-amber-400" />
                  <span>{result.processing_time_ms}ms</span>
                </div>
              </div>

              {/* Generated Instagram DM Box */}
              <div className="p-4 rounded-xl bg-gradient-to-br from-[#141824] to-[#10131d] border border-amber-500/30 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-amber-400 flex items-center space-x-1.5 uppercase tracking-wider">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Synthesized Instagram DM Response</span>
                  </span>
                  <div className="flex items-center space-x-1 text-[11px] text-emerald-400 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{result.fact_validation_passed ? "Fact Checked" : "Fallback Applied"}</span>
                  </div>
                </div>

                <p className="text-xs text-slate-100 whitespace-pre-wrap leading-relaxed pt-1">
                  {result.generated_reply}
                </p>
              </div>

              {/* Factual Validation Details */}
              <div className="p-3.5 rounded-xl bg-[#141824]/60 border border-[#23283a] space-y-2">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-semibold text-slate-200">
                    Anti-Hallucination Firewall Result
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 leading-relaxed">
                  {result.fact_validation_passed ? (
                    <p className="text-emerald-400">
                      ✓ Automated validation passed against the available catalogue context. Review the reply before enabling live automation.
                    </p>
                  ) : (
                    <p className="text-amber-400">
                      ⚠ Hallucination firewall activated. Fallback response applied: {result.validation_flags.join(", ")}
                    </p>
                  )}
                </div>
              </div>

              {/* Matched Catalogue Products */}
              {result.retrieved_products.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-300 block">
                    Grounded Product Facts Injected into Context:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {result.retrieved_products.map((prod) => (
                      <div
                        key={prod.id}
                        className="p-2.5 rounded-xl bg-[#141824] border border-[#23283a] flex items-center space-x-3"
                      >
                        <div className="w-12 h-12 rounded-lg bg-[#1c2130] overflow-hidden shrink-0">
                          {prod.images?.[0] ? (
                            <img
                              src={prod.images[0].image_url}
                              alt={prod.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-slate-600">
                              <Tag className="w-4 h-4" />
                            </div>
                          )}
                        </div>
                        <div className="min-w-0">
                          <h4 className="text-xs font-bold text-white truncate">{prod.name}</h4>
                          <div className="flex items-center space-x-2 text-[10px] text-slate-400 mt-0.5">
                            <span className="text-amber-400 font-semibold">{formatCurrency(prod.price)}</span>
                            <span>•</span>
                            <span>{prod.gold_purity || "22K"}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-center p-6 space-y-2 text-slate-500">
              <Bot className="w-10 h-10 text-slate-600" />
              <p className="text-xs">Click "Simulate AI Execution" or pick a sample test scenario above to see intent parsing, vision matching, and factual verification.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
