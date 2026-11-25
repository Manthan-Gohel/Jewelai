import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JewelAI — Official Instagram AI Assistant",
  description: "Enterprise Instagram AI sales assistant for luxury jewellery brands powered by official Meta Instagram APIs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#08090c] text-slate-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
