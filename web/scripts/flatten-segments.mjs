// Post-build step for the static export.
//
// The client router prefetches route segments from dotted file names (e.g. `/pt/models/__next.$d$lang.models.__PAGE__.txt`),
// but `next build` with `output: "export"` writes them as nested folders (`/pt/models/__next.$d$lang/models/__PAGE__.txt`).
// Static hosts don't map one to the other, so prefetches 404. We copy every nested segment file to its dotted name.
import { copyFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

const OUT = path.resolve(import.meta.dirname, "..", "out");
let copied = 0;

function walk(dir) {
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    if (!statSync(full).isDirectory()) continue;
    if (entry.startsWith("__next.")) flatten(full, dir, entry);
    else walk(full);
  }
}

function flatten(segmentDir, parent, prefix) {
  for (const entry of readdirSync(segmentDir)) {
    const full = path.join(segmentDir, entry);
    const name = `${prefix}.${entry}`;
    if (statSync(full).isDirectory()) flatten(full, parent, name);
    else {
      copyFileSync(full, path.join(parent, name));
      copied += 1;
    }
  }
}

walk(OUT);
console.log(`flatten-segments: ${copied} prefetch files copied`);
