import { LANGS, isLang } from "@/lib/i18n";
import { OG_SIZE, renderOgImage } from "@/lib/og";

// Rendered once at build time (static export)
export const dynamic = "force-static";

export function generateStaticParams() {
  return LANGS.map((lang) => ({ lang }));
}

export const size = OG_SIZE;
export const contentType = "image/png";
export const alt = "Brasileirão 2026: chances de Libertadores e rebaixamento / Libertadores and relegation chances";

export default async function Image({ params }: { params: Promise<{ lang: string }> }) {
  const { lang } = await params;
  return renderOgImage(isLang(lang) ? lang : "pt");
}
