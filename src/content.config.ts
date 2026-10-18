import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: z.object({
    title: z.string(),
    // the <title>/meta keeps the long keyword-bearing title; the page can show a shorter
    // one so a headline never wraps past two lines on a phone
    displayTitle: z.string().optional(),
    slug: z.string(),
    date: z.coerce.date(),
    description: z.string(),
    bloggerId: z.string().optional(),
    bloggerUrl: z.string().optional(),
    tags: z.array(z.string()).default([]),
    // where the guide sits in the reader's first months — drives the grouped index
    topic: z.enum(['arriving', 'money', 'home', 'health', 'daily']).default('daily'),
    hero: z
      .object({
        src: z.string(),
        alt: z.string().default(''),
        credit: z.string().default(''),
        creditUrl: z.string().default(''),
      })
      .optional(),
    // the one number a reader came for — rendered as the key fact on the card and page
    keyFact: z.object({ label: z.string(), value: z.string() }).optional(),
    sourcesCheckedOn: z.coerce.date().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { posts };
