import type { FastifyInstance } from "fastify";
import { z } from "zod";
import { getPool } from "@unified-inbox/shared";

const threadQuerySchema = z.object({
  provider: z.enum(["gmail", "slack"]).optional(),
  unreadOnly: z
    .string()
    .optional()
    .transform((value) => value === "true"),
  limit: z
    .string()
    .optional()
    .transform((value) => Number(value ?? "25"))
    .pipe(z.number().int().positive().max(100)),
});

const messageQuerySchema = z.object({
  limit: z
    .string()
    .optional()
    .transform((value) => Number(value ?? "100"))
    .pipe(z.number().int().positive().max(200)),
});

export async function threadRoutes(fastify: FastifyInstance): Promise<void> {
  const pool = getPool();

  fastify.get("/", { preHandler: [fastify.authenticate] }, async (request) => {
    const userId = request.user.userId;
    const query = threadQuerySchema.parse(request.query);

    const result = await pool.query(
      `SELECT
         t.id,
         t.provider_thread_id,
         t.subject,
         t.last_message_at,
         t.is_unread,
         t.summary,
         a.provider,
         a.external_account_id
       FROM threads t
       INNER JOIN accounts a ON a.id = t.account_id
       WHERE t.user_id = $1
         AND ($2::text IS NULL OR a.provider = $2)
         AND ($3::boolean = FALSE OR t.is_unread = TRUE)
       ORDER BY t.last_message_at DESC NULLS LAST
       LIMIT $4`,
      [userId, query.provider ?? null, query.unreadOnly ?? false, query.limit],
    );

    return { threads: result.rows };
  });

  fastify.get("/:threadId/messages", { preHandler: [fastify.authenticate] }, async (request, reply) => {
    const userId = request.user.userId;
    const params = z.object({ threadId: z.string().uuid() }).parse(request.params);
    const query = messageQuerySchema.parse(request.query);

    const exists = await pool.query(
      `SELECT id
       FROM threads
       WHERE id = $1 AND user_id = $2`,
      [params.threadId, userId],
    );

    if (!exists.rowCount) {
      return reply.code(404).send({ error: "Thread not found" });
    }

    const messages = await pool.query(
      `SELECT id, provider_message_id, sender, recipients, body_text, body_html, sent_at, is_unread, direction
       FROM messages
       WHERE thread_id = $1
       ORDER BY sent_at DESC
       LIMIT $2`,
      [params.threadId, query.limit],
    );

    return { messages: messages.rows };
  });

  fastify.post("/:threadId/mark-read", { preHandler: [fastify.authenticate] }, async (request, reply) => {
    const userId = request.user.userId;
    const params = z.object({ threadId: z.string().uuid() }).parse(request.params);

    const thread = await pool.query(
      `SELECT id
       FROM threads
       WHERE id = $1 AND user_id = $2`,
      [params.threadId, userId],
    );

    if (!thread.rowCount) {
      return reply.code(404).send({ error: "Thread not found" });
    }

    await pool.query(
      `UPDATE threads
       SET is_unread = FALSE,
           updated_at = NOW()
       WHERE id = $1`,
      [params.threadId],
    );

    await pool.query(
      `UPDATE messages
       SET is_unread = FALSE
       WHERE thread_id = $1`,
      [params.threadId],
    );

    return reply.send({ ok: true });
  });
}
