import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://www.darlingtree.com',
  compressHTML: true,
  build: {
    inlineStylesheets: 'auto',
  },
});
