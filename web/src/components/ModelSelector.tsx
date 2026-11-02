"use client";

import { getDict, type Lang } from "@/lib/i18n";

import { useModel } from "./ModelProvider";

export function ModelSelector({ lang }: { lang: Lang }) {
  const t = getDict(lang);
  const { model, models, setModel } = useModel();
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-muted">{t.model}:</span>
      <div className="inline-flex rounded-lg border border-border bg-surface p-0.5" role="radiogroup">
        {models.map((m) => (
          <button
            key={m}
            role="radio"
            aria-checked={m === model}
            onClick={() => setModel(m)}
            title={t.models[m].blurb}
            className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
              m === model ? "bg-accent text-white" : "text-muted hover:text-foreground"
            }`}
          >
            {t.models[m].name}
          </button>
        ))}
      </div>
      <span className="hidden text-xs text-muted sm:inline">{t.models[model].blurb}</span>
    </div>
  );
}
