import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  MCP_PORT: z.coerce.number().int().positive().default(4000),
  DATABASE_URL: z.string().min(1),
  ENCRYPTION_KEY: z.string().min(44),
  GMAIL_CLIENT_ID: z.string().optional().default(""),
  GMAIL_CLIENT_SECRET: z.string().optional().default(""),
  MCP_AUTH_TOKEN: z.string().optional(),
});

export const env = envSchema.parse(process.env);
