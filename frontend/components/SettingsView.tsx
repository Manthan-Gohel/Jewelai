"use client";

import React, { useState, useEffect } from "react";
import {
  Settings as SettingsIcon,
  Activity,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
} from "lucide-react";
import { BusinessSettings, api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface SettingsViewProps {
  settings: BusinessSettings | null;
  onUpdateSettings: (data: Partial<BusinessSettings>) => Promise<void>;
}

export default function SettingsView({ settings, onUpdateSettings }: SettingsViewProps) {
  const [logs, setLogs] = useState<any[]>([]);
  const [tone, setTone] = useState(settings?.tone || "luxurious");
  const [businessName, setBusinessName] = useState(settings?.business_name || "");
  const [tagline, setTagline] = useState(settings?.tagline || "");
  const [contactPhone, setContactPhone] = useState(settings?.contact_phone || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadLogs = async () => {
    try {
      const data = await api.getActivityLogs();
      setLogs(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load audit logs.");
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    try {
      await onUpdateSettings({
        business_name: businessName,
        tagline: tagline,
        tone: tone,
        contact_phone: contactPhone,
      });
      alert("Settings saved successfully!");
    } catch (err) {
      alert("Failed to save: " + err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-serif font-bold text-white tracking-wide">
          Settings & Automation Audit Logs
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Configure business brand persona, escalation controls, and inspect real-time AI execution logs.
        </p>
      </div>

      {error && <p role="alert" className="text-sm text-rose-200">{error} Use Refresh audit logs to retry.</p>}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Brand Configuration (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-2xl bg-[#0f1118] border border-[#1e2333] p-5 space-y-4">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Brand Persona & Tone
              </h3>
            </div>

            <form onSubmit={handleSaveSettings} className="space-y-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Business Name</label>
                <input
                  type="text"
                  aria-label="Business Name"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Tagline</label>
                <input
                  type="text"
                  aria-label="Tagline"
                  value={tagline}
                  onChange={(e) => setTagline(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">AI Conversational Tone</label>
                <select
                  aria-label="AI Conversational Tone"
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white"
                >
                  <option value="luxurious">Luxurious & Prestigious</option>
                  <option value="elegant">Elegant & Polite</option>
                  <option value="warm">Warm & Welcoming</option>
                  <option value="formal">Traditional & Formal</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Customer Care Phone</label>
                <input
                  type="text"
                  aria-label="Customer Care Phone"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-white"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="w-full py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 text-xs font-bold transition-all disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Configuration"}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Automation Logs (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-2xl bg-[#0f1118] border border-[#1e2333] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-amber-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Automation & Fact Validation Audit Logs
                </h3>
              </div>
              <button onClick={loadLogs} className="text-[10px] text-amber-300 underline">Refresh audit logs</button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#1e2333] text-slate-400 text-[11px]">
                    <th className="pb-2 font-medium">Time</th>
                    <th className="pb-2 font-medium">Action</th>
                    <th className="pb-2 font-medium">Intent</th>
                    <th className="pb-2 font-medium">Latency</th>
                    <th className="pb-2 font-medium">Fact Validation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#171b26]">
                  {logs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-slate-500">
                        No activity logs recorded yet.
                      </td>
                    </tr>
                  ) : (
                    logs.map((l) => (
                      <tr key={l.id} className="hover:bg-[#121622] transition-colors">
                        <td className="py-2.5 text-slate-400 whitespace-nowrap">
                          {formatDate(l.created_at)}
                        </td>
                        <td className="py-2.5 font-semibold text-slate-200">
                          {l.action}
                        </td>
                        <td className="py-2.5 text-amber-300 capitalize">
                          {l.intent?.replace("_", " ") || "General"}
                        </td>
                        <td className="py-2.5 text-slate-400">
                          {l.latency_ms}ms
                        </td>
                        <td className="py-2.5">
                          {l.validation_passed ? (
                            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold inline-flex items-center space-x-1">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>Verified</span>
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold inline-flex items-center space-x-1">
                              <AlertTriangle className="w-3 h-3" />
                              <span>Escalated</span>
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
