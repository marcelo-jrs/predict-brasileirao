import type { Metadata } from "next";

import "../globals.css";

export const metadata: Metadata = {
  title: "Brasileirão 2026 · Previsões / Predictions",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="font-sans">{children}</body>
    </html>
  );
}
