import type { FastifyInstance } from "fastify";
import { z } from "zod";
import { ACCOUNT_SYNC_JOB_NAMES, getPool } from "@unified-inbox/shared";
import { accountSyncQueue } from "../queue";

const enqueueSyncSchema = z.object({
  accountId: z.string().uuid().optional(),
});

export async function syncRoutes(fastify: FastifyInstance): Promise<void> {
  const pool = getPool();

  fastify.post("/jobs", { preHandler: [fastify.authenticate] }, async (request, reply) => {
    const body = enqueueSyncSchema.parse(request.body ?? {});
    const userId = request.user.userId;

    if (body.accountId) {
      const account = await pool.query(
        `SELECT id
         FROM accounts
         WHERE id = $1 AND user_id = $2`,
        [body.accountId, userId],
      );

      if (!account.rowCount) {
        return reply.code(404).send({ error: "Account not found" });
      }
    }

    const job = await accountSyncQueue.add(ACCOUNT_SYNC_JOB_NAMES.MANUAL, {
      userId,
      accountId: body.accountId,
      reason: "manual",
    });

    return reply.code(202).send({
      queued: true,
      jobId: job.id,
    });
  });
}
