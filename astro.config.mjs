import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://kaiyun818.github.io',
  integrations: [sitemap()],
});
