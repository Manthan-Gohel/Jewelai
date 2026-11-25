import type { Metadata } from "next";

export const metadata: Metadata = { title: "Data-deletion instructions | JewelAI" };

export default function DataDeletionPage() {
  return <>
    <h1>Data-deletion instructions</h1>
    <p>Deleting your JewelAI data is a separate action from disconnecting Instagram.
      This installation does not offer an automatic deletion button or a Meta deletion callback.</p>
    <h2>Workspace owners</h2>
    <ol>
      <li>If you can sign in, open the Instagram connection screen and disconnect the account to stop new automated activity and clear the stored access token.</li>
      <li>Contact the organization that invited you through your existing support channel. Ask for deletion of your JewelAI workspace and connected Instagram data.</li>
      <li>Include your workspace email and Instagram username, and say whether you want the entire workspace or particular conversation records removed.
        Never send your password, access token or invitation code.</li>
      <li>The operator must verify your authority, confirm the scope and explain any records that cannot be removed and why.
        Request written confirmation when deletion is complete, including how backups and third-party copies are handled.</li>
    </ol>
    <h2>People who messaged a connected business</h2>
    <p>Contact that business through the Instagram account you messaged or its published privacy/support channel.
      Identify the conversation and request deletion from its JewelAI installation. You do not need a JewelAI login to make that request.</p>
    <h2>What the request covers</h2>
    <p>Ask the operator to review account/profile records, stored tokens, messages and customer profiles, comments,
      webhook payloads, automation logs, usage records, queued work and backups associated with your request.
      Deleting records here does not itself remove messages from Instagram or guarantee deletion from external providers.</p>
    <h2>Public-launch requirement</h2>
    <p>The operator must replace the pilot contact instructions with a working public contact method,
      publish its retention/deletion schedule and test its deletion process before this page is submitted as a production policy URL.</p>
  </>;
}
