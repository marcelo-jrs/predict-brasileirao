import { OG_SIZE, renderOgImage } from "@/lib/og";

// Rendered once at build time (static export)
export const dynamic = "force-static";
export const size = OG_SIZE;
export const contentType = "image/png";
export const alt = "Brasileirão 2026: chances de Libertadores e rebaixamento";

export default function Image() {
  return renderOgImage("pt");
}
