import { renderOgImage } from "@/lib/og";

// Social preview image for "/", written as a static /og.png at build time
export const dynamic = "force-static";

export function GET() {
  return renderOgImage("pt");
}
