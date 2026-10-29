import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap'; // 新增：引入 sitemap

export default defineConfig({
  site: 'https://kaiyun818.github.io',
  integrations: [sitemap()], // 新增：自动生成网站地图
});
