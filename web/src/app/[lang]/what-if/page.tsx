import type { Metadata } from "next";

import { WhatIfView } from "@/components/WhatIfView";
import { getFixtures, getMeta, getScoreMatrices, getScorelines, getTable } from "@/lib/data";
import { getDict, isLang } from "@/lib/i18n";

export async function generateMetadata({ params }: PageProps<"/[lang]/what-if">): Promise<Metadata> {
  const { lang } = await params;
  return isLang(lang) ? { title: getDict(lang).whatif.title } : {};
}

export default async function WhatIfPage({ params }: PageProps<"/[lang]/what-if">) {
  const { lang } = await params;
  if (!isLang(lang)) return null;
  return (
    <WhatIfView
      lang={lang}
      meta={getMeta()}
      table={getTable()}
      fixtures={getFixtures()}
      scorelines={getScorelines()}
      scoreMatrices={getScoreMatrices()}
    />
  );
}
