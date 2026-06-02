import type { NextConfig } from 'next'
import path from 'path'

const nextConfig: NextConfig = {
  turbopack: {
    // Point Next.js to the monorepo root so it doesn't get confused by
    // multiple lockfiles in parent directories.
    root: path.resolve(__dirname, '../..'),
  },
}

export default nextConfig
