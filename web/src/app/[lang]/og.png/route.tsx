import { LANGS, isLang } from "@/lib/i18n";
import { renderOgImage } from "@/lib/og";

// Social preview image, written as a static /<lang>/og.png at build time
export const dynamic = "force-static";

export function generateStaticParams() {
  return LANGS.map((lang) => ({ lang }));
}

export async function GET(_request: Request, { params }: { params: Promise<{ lang: string }> }) {
  const { lang } = await params;
  return renderOgImage(isLang(lang) ? lang : "pt");
}
