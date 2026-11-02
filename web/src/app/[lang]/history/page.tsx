import type { Metadata } from "next";

import { HistoryView } from "@/components/HistoryView";
import { getAllHistory, getAllPredictions, getMeta, getTable } from "@/lib/data";
import { getDict, isLang } from "@/lib/i18n";

export async function generateMetadata({ params }: PageProps<"/[lang]/history">): Promise<Metadata> {
  const { lang } = await params;
  return isLang(lang) ? { title: getDict(lang).historyPage.title } : {};
}

export default async function HistoryPage({ params }: PageProps<"/[lang]/history">) {
  const { lang } = await params;
  if (!isLang(lang)) return null;
  const meta = getMeta();
  return (
    <HistoryView
      lang={lang}
      meta={meta}
      table={getTable()}
      history={getAllHistory(meta.models)}
      predictions={getAllPredictions(meta.models)}
    />
  );
}
