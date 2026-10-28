import { defineCollection, z } from 'astro:content';

const matches = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.string(),
    home: z.string(),
    away: z.string(),
    homeScore: z.number(),
    awayScore: z.number(),
    league: z.string().optional(),
    venue: z.string().optional(),
  }),
});

export const collections = { matches };
