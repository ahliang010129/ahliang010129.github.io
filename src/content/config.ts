import { defineCollection, z } from 'astro:content';

const matches = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    home: z.string(),
    away: z.string(),
    homeScore: z.number(),
    awayScore: z.number(),
    league: z.string().optional(),
    sport: z.string().optional(), // 新增
    venue: z.string().optional(),
  }),
});

export const collections = { matches };
