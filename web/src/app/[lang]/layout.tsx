import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { notFound } from "next/navigation";

import "../globals.css";
import { Header } from "@/components/Header";
import { ModelProvider } from "@/components/ModelProvider";
import { getMeta } from "@/lib/data";
import { formatDate } from "@/lib/format";
import { LANGS, getDict, isLang } from "@/lib/i18n";
import { OG_SIZE } from "@/lib/og";
import { REPO_URL, SITE_URL } from "@/lib/site";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const dynamicParams = false;

export function generateStaticParams() {
  return LANGS.map((lang) => ({ lang }));
}

export async function generateMetadata({ params }: LayoutProps<"/[lang]">): Promise<Metadata> {
  const { lang } = await params;
  if (!isLang(lang)) return {};
  const t = getDict(lang);
  return {
    metadataBase: new URL(SITE_URL),
    title: { default: t.siteTitle, template: `%s · ${t.siteTitle}` },
    description: t.siteDescription,
    alternates: { languages: { "pt-BR": "/pt/", en: "/en/" } },
    openGraph: {
      type: "website",
      siteName: t.siteTitle,
      title: t.siteTitle,
      description: t.siteDescription,
      locale: lang === "pt" ? "pt_BR" : "en_GB",
      url: `/${lang}/`,
      images: [{ url: `/${lang}/og.png`, ...OG_SIZE, alt: t.siteDescription }],
    },
    twitter: {
      card: "summary_large_image",
      title: t.siteTitle,
      description: t.siteDescription,
      images: [`/${lang}/og.png`],
    },
  };
}

export default async function LangLayout({ children, params }: LayoutProps<"/[lang]">) {
  const { lang } = await params;
  if (!isLang(lang)) notFound();
  const t = getDict(lang);
  const meta = getMeta();

  return (
    <html lang={lang === "pt" ? "pt-BR" : "en"} className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
      <body className="flex min-h-screen flex-col font-sans">
        <ModelProvider models={meta.models} defaultModel={meta.default_model}>
          <Header lang={lang} />
          <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">{children}</main>
          <footer className="border-t border-border py-6 text-center text-xs text-muted">
            <p>
              {t.freshness(formatDate(meta.data_through, lang), meta.games_played, meta.games_remaining)} ·{" "}
              {t.updated(formatDate(meta.generated_at.slice(0, 10), lang))}
            </p>
            <p className="mt-1">
              {t.footer.source}{" "}
              <a href={REPO_URL} className="underline hover:text-foreground">
                {t.footer.code}
              </a>
            </p>
          </footer>
        </ModelProvider>
      </body>
    </html>
  );
}
