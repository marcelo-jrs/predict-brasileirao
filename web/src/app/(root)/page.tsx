import Link from "next/link";

import { LanguageRedirect } from "./LanguageRedirect";

// "/" has no content of its own: send visitors to /pt/ or /en/ based on their browser language.
export default function RootPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 text-center">
      <noscript>
        <meta httpEquiv="refresh" content="0; url=/pt/" />
      </noscript>
      <LanguageRedirect />
      <p className="text-lg font-semibold">⚽ Brasileirão 2026</p>
      <p className="flex gap-4">
        <Link className="underline" href="/pt/">
          Português
        </Link>
        <Link className="underline" href="/en/">
          English
        </Link>
      </p>
    </main>
  );
}
