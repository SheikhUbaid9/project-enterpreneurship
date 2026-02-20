import type { Pool } from "pg";
import { z } from "zod";
import { getPool } from "@unified-inbox/shared";
import { env } from "./config";
import { sendGmailReply } from "./providers/gmail";
import { sendSlackReply } from "./providers/slack";

type JsonObject = Record<string, unknown>;

const getUnreadSchema = z.object({
  user_id: z.string().uuid(),
  provider: z.enum(["gmail", "slack"]).optional(),
  limit: z.coerce.number().int().positive().max(100).default(25),
});

const summarizeSchema = z.object({
  user_id: z.string().uuid(),
  provider: z.enum(["gmail", "slack"]).optional(),
  thread_ids: z.array(z.string().uuid()).optional(),
  limit: z.coerce.number().int().positive().max(25).default(10),
});

const sendReplySchema = z.object({
  user_id: z.string().uuid(),
  thread_id: z.string().uuid(),
  body: z.string().min(1).max(5000),
});

const TOOL_DEFINITIONS = [
  {
    name: "get_unread_messages",
    description: "Fetch unread messages from unified inbox (Gmail and Slack).",
    inputSchema: {
      type: "object",
      required: ["user_id"],
      properties: {
        user_id: { type: "string", format: "uuid" },
        provider: { type: "string", enum: ["gmail", "slack"] },
        limit: { type: "integer", minimum: 1, maximum: 100, default: 25 },
      },
    },
  },
  {
    name: "summarize_threads",
    description: "Summarize recent unified inbox threads for one user.",
    inputSchema: {
      type: "object",
      required: ["user_id"],
      properties: {
        user_id: { type: "string", format: "uuid" },
        provider: { type: "string", enum: ["gmail", "slack"] },
        thread_ids: { type: "array", items: { type: "string", format: "uuid" } },
        limit: { type: "integer", minimum: 1, maximum: 25, default: 10 },
      },
    },
  },
  {
    name: "send_reply",
    description: "Send a reply into a Gmail or Slack thread.",
    inputSchema: {
      type: "object",
      required: ["user_id", "thread_id", "body"],
      properties: {
        user_id: { type: "string", format: "uuid" },
        thread_id: { type: "string", format: "uuid" },
        body: { type: "string", minLength: 1, maxLength: 5000 },
      },
    },
  },
] as const;

function truncate(value: string | null | undefined, max = 120): string {
  const v = (value ?? "").replace(/\s+/g, " ").trim();
  if (!v) {
    return "(empty)";
  }

  if (v.length <= max) {
    return v;
  }

  return `${v.slice(0, max)}...`;
}

async function logToolCall(
  pool: Pool,
  params: {
    userId: string | null;
    toolName: string;
    args: JsonObject;
    status: "success" | "error";
    result?: unknown;
    errorMessage?: string;
  },
): Promise<void> {
  await pool.query(
    `INSERT INTO tool_calls (user_id, tool_name, args, status, result, error_message)
     VALUES ($1, $2, $3::jsonb, $4, $5::jsonb, $6)`,
    [
      params.userId,
      params.toolName,
      JSON.stringify(params.args),
      params.status,
      params.result === undefined ? null : JSON.stringify(params.result),
      params.errorMessage ?? null,
    ],
  );
}

export async function getUnreadMessages(args: unknown): Promise<JsonObject> {
  const pool = getPool();
  const input = getUnreadSchema.parse(args);

  try {
    const result = await pool.query(
      `SELECT
         m.id,
         m.thread_id,
         m.provider_message_id,
         m.sender,
         m.recipients,
         m.body_text,
         m.sent_at,
         a.provider,
         t.subject
       FROM messages m
       INNER JOIN threads t ON t.id = m.thread_id
       INNER JOIN accounts a ON a.id = m.account_id
       WHERE t.user_id = $1
         AND m.is_unread = TRUE
         AND ($2::text IS NULL OR a.provider = $2)
       ORDER BY m.sent_at DESC
       LIMIT $3`,
      [input.user_id, input.provider ?? null, input.limit],
    );

    const payload = {
      unread_messages: result.rows,
      count: result.rowCount,
    };

    await logToolCall(pool, {
      userId: input.user_id,
      toolName: "get_unread_messages",
      args: input,
      status: "success",
      result: payload,
    });

    return payload;
  } catch (error) {
    await logToolCall(pool, {
      userId: input.user_id,
      toolName: "get_unread_messages",
      args: input,
      status: "error",
      errorMessage: error instanceof Error ? error.message : "Unknown error",
    });
    throw error;
  }
}

export async function summarizeThreads(args: unknown): Promise<JsonObject> {
  const pool = getPool();
  const input = summarizeSchema.parse(args);

  try {
    const result = await pool.query(
      `SELECT
         t.id,
         t.subject,
         a.provider,
         t.last_message_at,
         t.is_unread,
         (
           SELECT json_agg(x ORDER BY x.sent_at DESC)
           FROM (
             SELECT m.sender, m.body_text, m.sent_at
             FROM messages m
             WHERE m.thread_id = t.id
             ORDER BY m.sent_at DESC
             LIMIT 3
           ) x
         ) AS last_messages
       FROM threads t
       INNER JOIN accounts a ON a.id = t.account_id
       WHERE t.user_id = $1
         AND ($2::text IS NULL OR a.provider = $2)
         AND (
           $3::uuid[] IS NULL
           OR t.id = ANY($3)
         )
       ORDER BY t.last_message_at DESC NULLS LAST
       LIMIT $4`,
      [input.user_id, input.provider ?? null, input.thread_ids ?? null, input.limit],
    );

    const summaries = (result.rows as Array<{
      id: string;
      subject: string | null;
      provider: "gmail" | "slack";
      is_unread: boolean;
      last_messages: Array<{ sender: string; body_text: string | null; sent_at: string }> | null;
    }>).map((thread) => {
      const snippets = (thread.last_messages ?? []).map(
        (message) => `${message.sender}: ${truncate(message.body_text, 80)}`,
      );

      return {
        thread_id: thread.id,
        provider: thread.provider,
        subject: thread.subject ?? "(no subject)",
        unread: thread.is_unread,
        summary: snippets.join(" | ") || "No recent messages",
      };
    });

    const text = summaries
      .map(
        (item, idx) =>
          `${idx + 1}. [${item.provider}] ${item.subject} | unread=${item.unread} | ${item.summary}`,
      )
      .join("\n");

    const payload = {
      summaries,
      summary_text: text,
    };

    await logToolCall(pool, {
      userId: input.user_id,
      toolName: "summarize_threads",
      args: input,
      status: "success",
      result: payload,
    });

    return payload;
  } catch (error) {
    await logToolCall(pool, {
      userId: input.user_id,
      toolName: "summarize_threads",
      args: input,
      status: "error",
      errorMessage: error instanceof Error ? error.message : "Unknown error",
    });
    throw error;
  }
}

export async function sendReply(args: unknown): Promise<JsonObject> {
  const pool = getPool();
  const input = sendReplySchema.parse(args);

  try {
    const threadResult = await pool.query(
      `SELECT
         t.id,
         t.subject,
         t.provider_thread_id,
         t.account_id,
         a.provider,
         a.access_token_encrypted,
         a.refresh_token_encrypted,
         latest.sender AS latest_sender,
         latest.provider_message_id AS latest_provider_message_id
       FROM threads t
       INNER JOIN accounts a ON a.id = t.account_id
       LEFT JOIN LATERAL (
         SELECT sender, provider_message_id
         FROM messages
         WHERE thread_id = t.id
         ORDER BY sent_at DESC
         LIMIT 1
       ) latest ON TRUE
       WHERE t.id = $1
         AND t.user_id = $2`,
      [input.thread_id, input.user_id],
    );

    if (!threadResult.rowCount) {
      throw new Error("Thread not found for user");
    }

    const thread = threadResult.rows[0] as {
      id: string;
      subject: string | null;
      provider_thread_id: string;
      account_id: string;
      provider: "gmail" | "slack";
      access_token_encrypted: string;
      refresh_token_encrypted: string | null;
      latest_sender: string | null;
      latest_provider_message_id: string | null;
    };

    let providerMessageId = "";

    if (thread.provider === "gmail") {
      providerMessageId = await sendGmailReply({
        accessTokenEncrypted: thread.access_token_encrypted,
        refreshTokenEncrypted: thread.refresh_token_encrypted,
        threadProviderId: thread.provider_thread_id,
        recipient: thread.latest_sender ?? "",
        subject: thread.subject,
        body: input.body,
        inReplyToProviderMessageId: thread.latest_provider_message_id,
        gmailClientId: env.GMAIL_CLIENT_ID,
        gmailClientSecret: env.GMAIL_CLIENT_SECRET,
      });
    }

    if (thread.provider === "slack") {
      providerMessageId = await sendSlackReply({
        accessTokenEncrypted: thread.access_token_encrypted,
        providerThreadId: thread.provider_thread_id,
        body: input.body,
      });
    }

    await pool.query(
      `INSERT INTO messages (
        thread_id,
        account_id,
        provider_message_id,
        sender,
        recipients,
        body_text,
        sent_at,
        is_unread,
        direction
      )
      VALUES ($1, $2, $3, $4, $5::text[], $6, NOW(), FALSE, 'outbound')`,
      [input.thread_id, thread.account_id, providerMessageId, "assistant", [], input.body],
    );

    await pool.query(
      `UPDATE threads
       SET last_message_at = NOW(),
           is_unread = FALSE,
           updated_at = NOW()
       WHERE id = $1`,
      [input.thread_id],
    );

    const payload = {
      ok: true,
      provider: thread.provider,
      provider_message_id: providerMessageId,
    };

    await logToolCall(pool, {
      userId: input.user_id,
      toolName: "send_reply",
      args: input,
      status: "success",
      result: payload,
    });

    return payload;
  } catch (error) {
    await logToolCall(pool, {
      userId: input.user_id,
      toolName: "send_reply",
      args: input,
      status: "error",
      errorMessage: error instanceof Error ? error.message : "Unknown error",
    });
    throw error;
  }
}

export function getToolDefinitions() {
  return TOOL_DEFINITIONS;
}
