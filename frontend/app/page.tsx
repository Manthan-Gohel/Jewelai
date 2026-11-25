"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import OverviewView from "@/components/OverviewView";
import InboxView from "@/components/InboxView";
import CatalogueView from "@/components/CatalogueView";
import PlaygroundView from "@/components/PlaygroundView";
import KnowledgeView from "@/components/KnowledgeView";
import InstagramView from "@/components/InstagramView";
import SettingsView from "@/components/SettingsView";
import MediaLinkingView from "@/components/MediaLinkingView";
import AuthView from "@/components/AuthView";
import { OverviewMetrics, BusinessSettings, InstagramStatus, User, ApiError, api } from "@/lib/api";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [metrics, setMetrics] = useState<OverviewMetrics | null>(null);
  const [settings, setSettings] = useState<BusinessSettings | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [loading, setLoading] = useState(false);
  const [connection, setConnection] = useState<InstagramStatus | null>(null);
  const [error, setError] = useState("");

  const loadInitialData = async () => {
    setLoading(true);
    setError("");
    try {
      const status = await api.getInstagramStatus();
      setConnection(status);
      if (!status.account?.is_connected) {
        setMetrics(null);
        setSettings(null);
        return;
      }
      const [m, s] = await Promise.all([
        api.getOverview(),
        api.getSettings(),
      ]);
      setMetrics(m);
      setSettings(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "We could not load your workspace.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Remove the old browser-readable token; browser authentication now uses an HttpOnly cookie.
    localStorage.removeItem("jewelai_token");
    const expired = () => { setUser(null); setMetrics(null); setSettings(null); setConnection(null); };
    window.addEventListener("jewelai:session-expired", expired);
    api.getMe().then(setUser).catch((err) => {
      if (!(err instanceof ApiError && err.status === 401)) setError(err instanceof Error ? err.message : "Server unavailable.");
    }).finally(() => setCheckingSession(false));
    if (new URLSearchParams(window.location.search).get("instagram") === "connected") {
      setActiveTab("instagram");
      window.history.replaceState({}, "", "/");
    }
    return () => window.removeEventListener("jewelai:session-expired", expired);
  }, []);

  useEffect(() => { if (user) loadInitialData(); }, [user]);

  const handleLogout = async () => {
    try { await api.logout(); setUser(null); setMetrics(null); setSettings(null); setConnection(null); setError(""); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not sign out. Please try again."); }
  };

  const handleToggleAutoReply = async () => {
    if (!settings) return;
    const nextVal = !settings.auto_reply_enabled;
    try {
      const updated = await api.updateSettings({ auto_reply_enabled: nextVal });
      setSettings(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "We could not change automatic replies.");
    }
  };

  const handleUpdateSettings = async (data: Partial<BusinessSettings>) => {
    try {
      const updated = await api.updateSettings(data);
      setSettings(updated);
    } catch (err) {
      console.error("Failed to update settings:", err);
      throw err;
    }
  };

  if (checkingSession) return <main className="flex min-h-screen items-center justify-center bg-[#08090c] text-slate-300"><p role="status">Opening your workspace…</p></main>;
  if (!user) return <AuthView onAuthenticated={(authenticated) => { setError(""); setUser(authenticated); }} />;

  return (
    <div className="min-h-screen bg-[#08090c] text-slate-100 flex flex-col">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:bg-amber-300 focus:p-3 focus:text-slate-950">Skip to content</a>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1a1e2c] px-4 py-2 text-xs text-slate-400">
        <span>Signed in as {user.name}</span>
        <button onClick={handleLogout} className="min-h-11 px-3 text-slate-200 hover:text-amber-300">Sign out</button>
      </div>
      <Navbar
        settings={settings}
        isConnected={connection?.account?.is_connected ?? false}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onToggleAutoReply={handleToggleAutoReply}
      />

      <main id="main-content" className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {error && <div role="alert" className="mb-6 rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">{error}<button onClick={loadInitialData} className="ml-3 min-h-11 underline">Try again</button></div>}
        {loading ? <p role="status" className="py-12 text-center text-slate-400">Loading your workspace…</p> : !connection?.account?.is_connected ? <InstagramView onConnectionChange={loadInitialData} /> : <>
        {activeTab === "overview" && (
          <OverviewView
            metrics={metrics}
            settings={settings}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}
        {activeTab === "inbox" && <InboxView />}
        {activeTab === "catalogue" && <CatalogueView />}
        {activeTab === "posts" && <MediaLinkingView />}
        {activeTab === "playground" && <PlaygroundView />}
        {activeTab === "knowledge" && (
          <KnowledgeView
            settings={settings}
            onUpdateSettings={handleUpdateSettings}
          />
        )}
        {activeTab === "instagram" && <InstagramView onConnectionChange={loadInitialData} />}
        {activeTab === "settings" && (
          <SettingsView
            settings={settings}
            onUpdateSettings={handleUpdateSettings}
          />
        )}
        </>}
      </main>

      <footer className="border-t border-[#1a1e2c] py-4 text-center text-xs text-slate-500">
        JewelAI • Your jewellery business, connected.
        <nav aria-label="Policy pages" className="mt-2 flex flex-wrap justify-center gap-x-4 text-slate-300">
          <Link href="/privacy" className="inline-flex min-h-11 items-center underline">Privacy</Link>
          <Link href="/terms" className="inline-flex min-h-11 items-center underline">Terms</Link>
          <Link href="/data-deletion" className="inline-flex min-h-11 items-center underline">Data deletion</Link>
        </nav>
      </footer>
    </div>
  );
}
