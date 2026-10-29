import { getCollection } from 'astro:content';
import type { APIRoute } from 'astro';

export const GET: APIRoute = async () => {
  const matches = await getCollection('matches');
  const site = 'https://kaiyun818.github.io';

  const pages = matches.map((match) => {
    return `<url><loc>${site}/match/${match.slug}/</loc></url>`;
  });

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>${site}/</loc></url>
    ${pages.join('')}
  </urlset>`;

  return new Response(sitemap, {
    headers: {
      'Content-Type': 'application/xml',
    },
  });
};
