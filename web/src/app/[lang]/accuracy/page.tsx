import type { Metadata } from "next";

import { AccuracyView } from "@/components/AccuracyView";
import { getAccuracy } from "@/lib/data";
import { getDict, isLang } from "@/lib/i18n";

export async function generateMetadata({ params }: PageProps<"/[lang]/accuracy">): Promise<Metadata> {
  const { lang } = await params;
  return isLang(lang) ? { title: getDict(lang).accuracyPage.title } : {};
}

export default async function AccuracyPage({ params }: PageProps<"/[lang]/accuracy">) {
  const { lang } = await params;
  if (!isLang(lang)) return null;
  return <AccuracyView lang={lang} accuracy={getAccuracy()} />;
}
