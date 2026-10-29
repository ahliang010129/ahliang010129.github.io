import { defineCollection, z } from 'astro:content';

const matches = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    home: z.string().optional(),
    away: z.string().optional(),
    homeScore: z.number().optional(),
    awayScore: z.number().optional(),
    league: z.string().optional(),
    sport: z.string().optional(),
    venue: z.string().optional(),
    image: z.string().optional(), // 新增图片字段支持
  }),
});

export const collections = { matches };
