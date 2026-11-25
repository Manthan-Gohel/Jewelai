"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Instagram } from "lucide-react";
import { api } from "@/lib/api";

export default function InstagramCallbackPage() {
  const started = useRef(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // React StrictMode runs effects twice; an authorization code may be exchanged only once.
    if (started.current) return;
    started.current = true;
    const params = new URLSearchParams(window.location.search);
    window.history.replaceState({}, "", window.location.pathname);
    async function complete() {
      try {
        const pending = JSON.parse(sessionStorage.getItem("jewelai_oauth") || "null");
        sessionStorage.removeItem("jewelai_oauth");
        if (params.has("error")) throw new Error("Instagram sign-in was cancelled or permission was not granted. You can try again whenever you are ready.");
        const code = params.get("code");
        const state = params.get("state");
        if (!code || !state || !pending || pending.state !== state || !["login", "connect"].includes(pending.mode)) {
          throw new Error("This sign-in link has expired or belongs to a different browser. Please start again from your workspace.");
        }
        if (pending.mode === "login") await api.finishInstagramLogin(code, state);
        else await api.connectInstagram(code, state);
        window.location.replace("/?instagram=connected");
      } catch (err) {
        setError(err instanceof Error ? err.message : "We could not finish Instagram sign-in. Please try again.");
      }
    }
    complete();
  }, []);

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#08090c] px-4 text-slate-100">
      <section className="w-full max-w-md rounded-2xl border border-[#24293c] bg-[#0f1118] p-8 text-center">
        <Instagram aria-hidden="true" className="mx-auto mb-5 h-10 w-10 text-amber-300" />
        <h1 className="font-serif text-2xl font-bold">{error ? "Let’s try that again" : "Finishing your Instagram connection"}</h1>
        <p role={error ? "alert" : "status"} className="mt-4 text-sm leading-relaxed text-slate-300">{error || "Please keep this page open. We are securely connecting your account."}</p>
        {error && <Link href="/" className="mt-6 inline-flex min-h-12 items-center justify-center rounded-xl bg-amber-400 px-5 py-3 text-sm font-bold text-slate-950">Back to workspace</Link>}
      </section>
    </main>
  );
}
