// Adapted from RyanFitzgerald/devportfolio (MIT).
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: process.env.SITE_URL || process.env.CF_PAGES_URL || 'https://techyan-demo.pages.dev',
  base: process.env.SITE_BASE || '/',
  output: 'static',
  trailingSlash: 'always',
  vite: { plugins: [tailwindcss()] },
  build: { inlineStylesheets: 'auto' },
});
