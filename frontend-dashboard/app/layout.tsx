import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Multi-Platform Inbox Dashboard",
  description: "Premium dashboard for the Multi-Platform Inbox MCP Server.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
