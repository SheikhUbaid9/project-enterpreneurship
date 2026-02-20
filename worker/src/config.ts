import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  REDIS_URL: z.string().min(1),
  ENCRYPTION_KEY: z.string().min(44),
  GMAIL_CLIENT_ID: z.string().optional().default(""),
  GMAIL_CLIENT_SECRET: z.string().optional().default(""),
  SYNC_BATCH_SIZE: z.coerce.number().int().positive().max(200).default(25),
  SYNC_SCHEDULE_SECONDS: z.coerce.number().int().positive().default(300),
});

export const env = envSchema.parse(process.env);
