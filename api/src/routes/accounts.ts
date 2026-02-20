import type { FastifyInstance } from "fastify";
import { z } from "zod";
import { encryptSecret, getPool } from "@unified-inbox/shared";

const connectAccountSchema = z.object({
  provider: z.enum(["gmail", "slack"]),
  externalAccountId: z.string().min(1),
  accessToken: z.string().min(1),
  refreshToken: z.string().optional(),
  tokenExpiresAt: z.string().datetime().optional(),
  metadata: z.record(z.any()).optional(),
});

export async function accountRoutes(fastify: FastifyInstance): Promise<void> {
  const pool = getPool();

  fastify.post("/", { preHandler: [fastify.authenticate] }, async (request, reply) => {
    const body = connectAccountSchema.parse(request.body);
    const userId = request.user.userId;

    const tokenExpiresAt = body.tokenExpiresAt ? new Date(body.tokenExpiresAt) : null;

    const result = await pool.query(
      `INSERT INTO accounts (
        user_id,
        provider,
        external_account_id,
        access_token_encrypted,
        refresh_token_encrypted,
        token_expires_at,
        metadata,
        updated_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, NOW())
      ON CONFLICT (user_id, provider, external_account_id)
      DO UPDATE SET
        access_token_encrypted = EXCLUDED.access_token_encrypted,
        refresh_token_encrypted = EXCLUDED.refresh_token_encrypted,
        token_expires_at = EXCLUDED.token_expires_at,
        metadata = EXCLUDED.metadata,
        updated_at = NOW()
      RETURNING id, user_id, provider, external_account_id, token_expires_at, metadata, created_at, updated_at`,
      [
        userId,
        body.provider,
        body.externalAccountId,
        encryptSecret(body.accessToken),
        body.refreshToken ? encryptSecret(body.refreshToken) : null,
        tokenExpiresAt,
        JSON.stringify(body.metadata ?? {}),
      ],
    );

    return reply.code(201).send({ account: result.rows[0] });
  });

  fastify.get("/", { preHandler: [fastify.authenticate] }, async (request) => {
    const userId = request.user.userId;

    const result = await pool.query(
      `SELECT id, user_id, provider, external_account_id, token_expires_at, metadata, created_at, updated_at
       FROM accounts
       WHERE user_id = $1
       ORDER BY created_at DESC`,
      [userId],
    );

    return { accounts: result.rows };
  });
}
