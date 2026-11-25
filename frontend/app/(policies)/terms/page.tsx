import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Service terms | JewelAI" };

export default function TermsPage() {
  return <>
    <h1>Service terms</h1>
    <p>This page describes the intended use and limitations of the JewelAI staging software.
      Commercial terms, service commitments and jurisdiction-specific provisions must be agreed with the service operator before a production handoff.</p>
    <h2>Authorized business use</h2>
    <p>Use only a workspace and professional Instagram account that you are authorized to manage.
      Keep your login and invitation code private. Do not use the service for spam, prohibited content,
      unauthorized access or activity that violates Instagram permissions or applicable law.</p>
    <h2>Your catalogue and automated replies</h2>
    <p>You are responsible for the accuracy of prices, gold rates, stock, product specifications, contact details and policies you supply.
      Gold rates are maintained manually, not supplied by a live market feed.
      Test responses with your own catalogue and languages before enabling automatic replies. AI-generated responses can be wrong;
      human review and escalation remain necessary.</p>
    <h2>External services and availability</h2>
    <p>Instagram and AI features depend on Meta and Google services, valid permissions, account eligibility, provider quota and the operator&apos;s infrastructure.
      An Instagram sign-in button does not guarantee permission approval or message delivery.
      Reauthorization may be necessary when access expires or is revoked.</p>
    <h2>Privacy and ending use</h2>
    <p>Read the <Link href="/privacy">privacy notice</Link> before supplying personal data.
      You can disconnect Instagram from the connection screen.
      Disconnection is not data deletion; use the <Link href="/data-deletion">deletion instructions</Link> for that request.</p>
    <h2>Support and commercial agreement</h2>
    <p>Use your existing contact with the organization that invited you during the pilot.
      No payment, refund, uptime, liability or support-response commitment is established by this source distribution.</p>
  </>;
}
