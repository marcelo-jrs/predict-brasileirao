"use client";

import { useEffect } from "react";

export function LanguageRedirect() {
  useEffect(() => {
    const lang = navigator.language?.toLowerCase().startsWith("pt") ? "pt" : "en";
    window.location.replace(`/${lang}/`);
  }, []);
  return null;
}
