import type { Metadata } from "next";

import "../globals.css";
import { getDict } from "@/lib/i18n";
import { OG_SIZE } from "@/lib/og";
import { SITE_URL } from "@/lib/site";

const pt = getDict("pt");

// "/" only redirects to /pt/ or /en/, but link previews (LinkedIn, WhatsApp…) read this page without running JS
export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: pt.siteTitle,
  description: `${pt.siteDescription} / ${getDict("en").siteDescription}`,
  openGraph: {
    type: "website",
    siteName: pt.siteTitle,
    title: pt.siteTitle,
    description: pt.siteDescription,
    locale: "pt_BR",
    url: "/",
    images: [{ url: "/og.png", ...OG_SIZE, alt: pt.siteDescription }],
  },
  twitter: {
    card: "summary_large_image",
    title: pt.siteTitle,
    description: pt.siteDescription,
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="font-sans">{children}</body>
    </html>
  );
}
