import type { Metadata } from "next";

import { ModelsView } from "@/components/ModelsView";
import { getAllPredictions, getFixtures, getMeta, getTable } from "@/lib/data";
import { getDict, isLang } from "@/lib/i18n";

export async function generateMetadata({ params }: PageProps<"/[lang]/models">): Promise<Metadata> {
  const { lang } = await params;
  return isLang(lang) ? { title: getDict(lang).modelsPage.title } : {};
}

export default async function ModelsPage({ params }: PageProps<"/[lang]/models">) {
  const { lang } = await params;
  if (!isLang(lang)) return null;
  const meta = getMeta();
  return (
    <ModelsView
      lang={lang}
      meta={meta}
      table={getTable()}
      predictions={getAllPredictions(meta.models)}
      fixtures={getFixtures()}
    />
  );
}
