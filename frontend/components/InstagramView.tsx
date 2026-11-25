"use client";

import { useEffect, useState } from "react";
import { Instagram, RefreshCw, ShieldCheck, CheckCircle2 } from "lucide-react";
import { api, InstagramStatus } from "@/lib/api";

export default function InstagramView({ onConnectionChange }: { onConnectionChange?: () => void }) {
  const [status, setStatus] = useState<InstagramStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadStatus() {
    setLoading(true);
    setError("");
    try { setStatus(await api.getInstagramStatus()); }
    catch (err) { setError(err instanceof Error ? err.message : "We could not load your connection. Please try again."); }
    finally { setLoading(false); }
  }

  useEffect(() => { loadStatus(); }, []);

  async function connect() {
    setBusy(true);
    setError("");
    try {
      const result = await api.getInstagramOAuthUrl();
      sessionStorage.setItem("jewelai_oauth", JSON.stringify({ mode: "connect", state: result.state }));
      window.location.assign(result.url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "We could not open Instagram. Please try again.");
      setBusy(false);
    }
  }

  async function disconnect() {
    if (!window.confirm("Disconnect Instagram? Automatic replies will stop. Your catalogue and conversation history will be kept.")) return;
    setBusy(true);
    setError("");
    try {
      await api.disconnectInstagram();
      setNotice("Instagram disconnected. Automatic replies are off.");
      await loadStatus();
      onConnectionChange?.();
    } catch (err) { setError(err instanceof Error ? err.message : "We could not disconnect. Please try again."); }
    finally { setBusy(false); }
  }

  const account = status?.account;
  const connected = !!account?.is_connected;
  const expiresAt = account?.token_expires_at ? new Date(account.token_expires_at) : null;
  const expiresSoon = expiresAt && expiresAt.getTime() < Date.now() + 7 * 86400000;

  return (
    <section className="mx-auto max-w-3xl space-y-6" aria-labelledby="instagram-title" aria-busy={loading}>
      <div className="flex items-center justify-between gap-4">
        <div><h1 id="instagram-title" className="text-2xl font-serif font-bold text-white">Your Instagram connection</h1><p className="mt-2 text-sm text-slate-400">One secure connection. No API keys or access tokens to copy.</p></div>
        <button onClick={loadStatus} disabled={loading || busy} aria-label="Refresh Instagram connection" className="min-h-11 min-w-11 rounded-xl border border-[#24293c] p-3 text-slate-300 hover:text-amber-300 disabled:opacity-50"><RefreshCw aria-hidden="true" className={`h-5 w-5 ${loading ? "animate-spin" : ""}`} /></button>
      </div>
      {error && <p role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</p>}
      {notice && <p role="status" className="text-sm text-emerald-300">{notice}</p>}
      <div className="gold-card rounded-2xl p-6 sm:p-8">
        <Instagram aria-hidden="true" className="mb-5 h-10 w-10 text-amber-300" />
        <h2 className="text-lg font-semibold text-white">{loading ? "Checking your account…" : connected ? `@${account?.username}` : "Connect your business account"}</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-300">{connected ? "Your account is connected. You can manage customer messages, link products to posts, and choose when AI replies are enabled." : "Continue to Instagram, select your Business or Creator account, and allow the requested permissions. You will return here automatically."}</p>
        {connected && <p className="mt-4 flex items-center gap-2 text-sm text-emerald-300"><CheckCircle2 aria-hidden="true" className="h-4 w-4" />{account?.webhook_subscribed ? "Message and comment notifications enabled" : "Connection needs attention — please reconnect"}</p>}
        {expiresSoon && <p role="status" className="mt-4 text-sm text-amber-200">Your Instagram authorization expires soon. Reconnect now to avoid interrupted replies.</p>}
        <div className="mt-6 flex flex-wrap gap-3">
          <button onClick={connect} disabled={busy || loading || !status?.login_available} className="flex min-h-12 items-center justify-center gap-2 rounded-xl bg-amber-400 px-5 py-3 text-sm font-bold text-slate-950 hover:bg-amber-300 disabled:opacity-50"><Instagram aria-hidden="true" className="h-4 w-4" />{busy ? "Please wait…" : connected ? "Reconnect Instagram" : "Sign in with Instagram"}</button>
          {connected && <button onClick={disconnect} disabled={busy} className="min-h-12 rounded-xl border border-rose-400/30 px-5 py-3 text-sm text-rose-200 hover:bg-rose-400/10 disabled:opacity-50">Disconnect</button>}
        </div>
        {status && !status.login_available && <p className="mt-4 text-sm text-amber-200">Your administrator needs to finish Instagram setup before you can connect. You do not need to create API keys.</p>}
      </div>
      <div className="rounded-2xl border border-[#24293c] bg-[#0f1118] p-6">
        <h2 className="text-base font-semibold text-white">Before you connect</h2>
        <ol className="mt-4 list-decimal space-y-3 pl-5 text-sm leading-relaxed text-slate-300">
          <li>Use an Instagram Business or Creator account. Personal accounts need to be switched to a professional account first.</li>
          <li>Allow profile, messaging, and comment access on Instagram’s secure permissions screen.</li>
          <li>Upload your real catalogue, check your store details, and test a reply before turning on automatic responses.</li>
        </ol>
        <p className="mt-5 flex items-start gap-2 text-xs leading-relaxed text-slate-400"><ShieldCheck aria-hidden="true" className="h-4 w-4 shrink-0" />We never ask for your Instagram password. You can disconnect at any time. Instagram sign-in is available for an existing workspace after its first connection.</p>
      </div>
    </section>
  );
}
