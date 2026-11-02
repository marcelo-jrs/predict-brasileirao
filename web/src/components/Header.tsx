"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { getDict, type Lang } from "@/lib/i18n";

const PAGES = [
  ["", "home"],
  ["models/", "models"],
  ["history/", "history"],
  ["what-if/", "whatif"],
  ["accuracy/", "accuracy"],
  ["how-it-works/", "how"],
] as const;

export function Header({ lang }: { lang: Lang }) {
  const t = getDict(lang);
  const pathname = usePathname() ?? `/${lang}/`;
  const rest = pathname.replace(/^\/(pt|en)\/?/, "");
  const otherLang: Lang = lang === "pt" ? "en" : "pt";

  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Link href={`/${lang}/`} className="flex items-center gap-2 font-semibold">
          <span aria-hidden className="text-xl">⚽</span>
          <span>{t.siteTitle}</span>
        </Link>
        <Link
          href={`/${otherLang}/${rest}`}
          className="rounded-md border border-border px-2 py-1 text-xs text-muted hover:text-foreground"
          hrefLang={otherLang}
        >
          {t.switchLang}
        </Link>
      </div>
      <nav className="mx-auto max-w-6xl overflow-x-auto px-4">
        <ul className="flex gap-1 whitespace-nowrap text-sm">
          {PAGES.map(([path, key]) => {
            const active = rest === path || (path === "" && rest === "");
            return (
              <li key={key}>
                <Link
                  href={`/${lang}/${path}`}
                  className={`inline-block border-b-2 px-3 py-2 ${
                    active ? "border-accent font-medium text-foreground" : "border-transparent text-muted hover:text-foreground"
                  }`}
                >
                  {t.nav[key]}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
}
