import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@lexguard/shared"],
  output: "standalone",
  webpack: (config) => {
    config.resolve.alias.canvas = false;
    return config;
  },
};

export default nextConfig;
