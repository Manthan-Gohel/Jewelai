"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { Gem, Instagram, Loader2, ShieldCheck } from "lucide-react";
import { api, User } from "@/lib/api";

export default function AuthView({ onAuthenticated }: { onAuthenticated: (user: User) => void }) {
  const [registering, setRegistering] = useState(false);
  const [setup, setSetup] = useState<{ registration_requires_invite: boolean; instagram_login_available: boolean } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getSetup().then(setSetup).catch(() => setError("We could not reach your workspace. Please try again shortly."));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const email = String(form.get("email")).trim();
      const password = String(form.get("password"));
      const result = registering
        ? await api.register({ name: String(form.get("name")).trim(), email, password, invite_code: String(form.get("invite_code") || "") })
        : await api.login(email, password);
      onAuthenticated(result.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "We could not sign you in. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function instagramLogin() {
    setBusy(true);
    setError("");
    try {
      const result = await api.startInstagramLogin();
      sessionStorage.setItem("jewelai_oauth", JSON.stringify({ mode: "login", state: result.state }));
      window.location.assign(result.url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Instagram sign-in is unavailable. Please use your email.");
      setBusy(false);
    }
  }

  const inputClass = "mt-2 w-full rounded-xl border border-[#2b3247] bg-[#141824] px-3 py-3 text-base text-white focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400";

  return (
    <main className="min-h-screen bg-[#08090c] px-4 py-12 text-slate-100 flex items-center justify-center">
      <section className="w-full max-w-md rounded-2xl border border-[#24293c] bg-[#0f1118] p-6 sm:p-8" aria-labelledby="auth-title">
        <div className="mb-6 flex items-center gap-3 text-amber-300"><Gem aria-hidden="true" className="h-8 w-8" /><span className="font-serif text-2xl font-bold">JewelAI</span></div>
        <h1 id="auth-title" className="font-serif text-2xl font-bold">{registering ? "Create your workspace" : "Welcome back"}</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-400">Manage your jewellery catalogue and Instagram conversations in one place.</p>

        {!registering && <>
          <button type="button" onClick={instagramLogin} disabled={busy || !setup?.instagram_login_available}
            className="mt-6 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl border border-amber-400/50 bg-amber-400/10 px-4 py-3 font-semibold text-amber-200 hover:bg-amber-400/20 disabled:opacity-50">
            <Instagram aria-hidden="true" className="h-5 w-5" /> Sign in with Instagram
          </button>
          <p className="mt-2 text-xs leading-relaxed text-slate-400">Already connected your business account? Sign in directly with Instagram. First time here? Use your workspace email below, then connect Instagram once.</p>
          {setup && !setup.instagram_login_available && <p className="mt-2 text-xs text-amber-200">Your administrator has not enabled Instagram sign-in yet. Email sign-in is available.</p>}
          <div className="my-6 flex items-center gap-3 text-xs text-slate-500"><span className="h-px flex-1 bg-[#24293c]" />or continue with email<span className="h-px flex-1 bg-[#24293c]" /></div>
        </>}

        <form onSubmit={submit} className="mt-6 space-y-4" aria-busy={busy}>
          {registering && <label className="block text-sm text-slate-300" htmlFor="name">Your name<input id="name" name="name" autoComplete="name" required maxLength={255} className={inputClass} disabled={busy} /></label>}
          <label className="block text-sm text-slate-300" htmlFor="email">Workspace email<input id="email" name="email" type="email" autoComplete="email" required className={inputClass} disabled={busy} /></label>
          <label className="block text-sm text-slate-300" htmlFor="password">Password<input id="password" name="password" type="password" autoComplete={registering ? "new-password" : "current-password"} minLength={registering ? 8 : 1} maxLength={72} required className={inputClass} disabled={busy} />{registering && <span className="mt-1 block text-xs text-slate-400">Use at least 8 characters.</span>}</label>
          {registering && setup?.registration_requires_invite && <label className="block text-sm text-slate-300" htmlFor="invite-code">Invitation code<input id="invite-code" name="invite_code" required autoComplete="off" className={inputClass} disabled={busy} /><span className="mt-1 block text-xs text-slate-400">Provided by your administrator.</span></label>}
          {error && <p role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-200">{error}</p>}
          <button type="submit" disabled={busy || (registering && !setup)} className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-amber-400 px-4 py-3 font-bold text-slate-950 hover:bg-amber-300 disabled:opacity-50">
            {busy && <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />}{busy ? "Please wait…" : registering ? "Create workspace" : "Sign in"}
          </button>
        </form>
        <button type="button" disabled={busy} onClick={() => { setRegistering(!registering); setError(""); }} className="mt-5 min-h-11 w-full text-sm text-amber-200 underline-offset-4 hover:underline">
          {registering ? "Already have an account? Sign in" : "New to JewelAI? Create your workspace"}
        </button>
        <p className="mt-3 text-center text-xs leading-relaxed text-slate-400">Trouble signing in? Contact the administrator who set up your workspace.</p>
        <nav aria-label="Policy pages" className="mt-3 flex flex-wrap justify-center gap-x-4 text-xs text-slate-300">
          <Link href="/privacy" className="inline-flex min-h-11 items-center underline">Privacy</Link>
          <Link href="/terms" className="inline-flex min-h-11 items-center underline">Terms</Link>
          <Link href="/data-deletion" className="inline-flex min-h-11 items-center underline">Data deletion</Link>
        </nav>
        <p className="mt-6 flex items-center justify-center gap-2 border-t border-[#24293c] pt-5 text-xs text-slate-400"><ShieldCheck aria-hidden="true" className="h-4 w-4 shrink-0" />Your Instagram password stays with Instagram.</p>
      </section>
    </main>
  );
}
