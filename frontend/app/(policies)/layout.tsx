import Link from "next/link";

export default function PolicyLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <Link href="/" className="inline-flex min-h-11 items-center text-amber-300 underline underline-offset-4">Back to JewelAI</Link>
      <aside aria-label="Deployment policy status" className="my-6 rounded-xl border border-amber-400/40 bg-amber-400/10 p-4 text-sm leading-relaxed text-amber-100">
        <strong>Operator review required before public launch.</strong> These notices describe the software, not a finalized legal agreement.
        The service operator must publish its legal identity, working privacy/support contact, retention and backup-deletion schedule,
        and applicable terms before using real customer data. Use synthetic data until that review is complete.
      </aside>
      <article className="space-y-5 text-sm leading-7 text-slate-300 [&_h1]:font-serif [&_h1]:text-3xl [&_h1]:font-bold [&_h1]:text-white [&_h2]:pt-3 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-white [&_a]:text-amber-300 [&_a]:underline [&_ul]:list-disc [&_ul]:space-y-2 [&_ul]:pl-6 [&_ol]:list-decimal [&_ol]:space-y-2 [&_ol]:pl-6">
        {children}
      </article>
      <nav aria-label="Policy pages" className="mt-10 flex flex-wrap gap-x-6 border-t border-[#1e2230] pt-4 text-sm text-amber-300">
        <Link className="inline-flex min-h-11 items-center underline" href="/privacy">Privacy</Link>
        <Link className="inline-flex min-h-11 items-center underline" href="/terms">Terms</Link>
        <Link className="inline-flex min-h-11 items-center underline" href="/data-deletion">Data deletion</Link>
      </nav>
    </main>
  );
}
