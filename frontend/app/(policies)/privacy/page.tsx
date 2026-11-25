import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Privacy notice | JewelAI" };

export default function PrivacyPage() {
  return <>
    <h1>Privacy notice</h1>
    <p>JewelAI helps an invited jewellery business manage its catalogue and conversations with customers on Instagram.
      The organization running this installation is responsible for its customer data and privacy requests.</p>
    <h2>Information the software processes</h2>
    <ul>
      <li>Workspace name, email address and a hashed password used for account access.</li>
      <li>The connected professional Instagram account identifier, profile details, encrypted access token and permission/connection status.</li>
      <li>Instagram message and comment content, customer identifiers, media links, conversation history and human-takeover status received by the service.</li>
      <li>Catalogue entries, linked posts, store details and knowledge documents supplied by the workspace.</li>
      <li>Webhook payloads, automation logs and AI usage records used for processing and troubleshooting.</li>
    </ul>
    <h2>How information is used and shared</h2>
    <p>Information is used to authenticate users, display the inbox, retrieve catalogue details and send replies when enabled.
      Meta processes Instagram authorization, messages and comments. When AI features run, relevant messages, recent conversation context,
      catalogue details and store knowledge may be sent to Google Gemini; image features may also process image URLs or image content.
      The operator must review the applicable provider terms and permissions before enabling those features.</p>
    <h2>Browser storage and security</h2>
    <p>The application uses HttpOnly cookies for workspace sessions and temporary Instagram authorization state.
      The callback uses temporary browser session storage to remember whether you are signing in or connecting Instagram.
      Stored Instagram tokens are encrypted; message content, webhook payloads and other database records are not application-level encrypted.
      The operator is responsible for HTTPS, infrastructure access controls, storage encryption and backups.</p>
    <h2>Retention, access and deletion</h2>
    <p>The software does not automatically expire stored conversations, webhook payloads or backups.
      Disconnecting Instagram stops the connection and clears the saved access token, but does not delete the workspace history.
      Follow the <Link href="/data-deletion">data-deletion instructions</Link> to request removal.
      Backup retention, legal retention and deletion completion must be confirmed by the operator.</p>
    <h2>Contact</h2>
    <p>During the staging pilot, contact the organization that invited you using your existing support channel.
      A dedicated public privacy contact and operator identity have not yet been configured in this source distribution.</p>
  </>;
}
