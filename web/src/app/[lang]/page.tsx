import { StandingsView } from "@/components/StandingsView";
import { getAllPredictions, getMeta, getTable } from "@/lib/data";
import { isLang } from "@/lib/i18n";

export default async function HomePage({ params }: PageProps<"/[lang]">) {
  const { lang } = await params;
  if (!isLang(lang)) return null;
  const meta = getMeta();
  return (
    <StandingsView lang={lang} meta={meta} table={getTable()} predictions={getAllPredictions(meta.models)} />
  );
}
