import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Fully static site: the data is precomputed by Python (web/public/data) and rebuilt on every data commit.
  output: "export",
  // /pt/ -> /pt/index.html, so the export works on any static host
  trailingSlash: true,
  images: { unoptimized: true },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
