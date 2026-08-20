import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Continuity - Reasoning Trail",
  description: "Live view into the Continuity incident-response agent's reasoning trail",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
