import type { Pool } from "pg";

export interface UpsertMessageInput {
  userId: string;
  accountId: string;
  providerThreadId: string;
  providerMessageId: string;
  subject: string | null;
  sender: string;
  recipients: string[];
  bodyText: string;
  sentAt: Date;
  isUnread: boolean;
  direction: "inbound" | "outbound";
}

export async function upsertThreadAndMessage(pool: Pool, input: UpsertMessageInput): Promise<void> {
  const threadResult = await pool.query(
    `INSERT INTO threads (
      user_id,
      account_id,
      provider_thread_id,
      subject,
      last_message_at,
      is_unread,
      updated_at
    )
    VALUES ($1, $2, $3, $4, $5, $6, NOW())
    ON CONFLICT (account_id, provider_thread_id)
    DO UPDATE SET
      subject = COALESCE(EXCLUDED.subject, threads.subject),
      last_message_at = GREATEST(threads.last_message_at, EXCLUDED.last_message_at),
      is_unread = threads.is_unread OR EXCLUDED.is_unread,
      updated_at = NOW()
    RETURNING id`,
    [
      input.userId,
      input.accountId,
      input.providerThreadId,
      input.subject,
      input.sentAt,
      input.isUnread,
    ],
  );

  const threadId = threadResult.rows[0].id as string;

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
    VALUES ($1, $2, $3, $4, $5::text[], $6, $7, $8, $9)
    ON CONFLICT (account_id, provider_message_id)
    DO UPDATE SET
      sender = EXCLUDED.sender,
      recipients = EXCLUDED.recipients,
      body_text = EXCLUDED.body_text,
      sent_at = EXCLUDED.sent_at,
      is_unread = EXCLUDED.is_unread,
      direction = EXCLUDED.direction`,
    [
      threadId,
      input.accountId,
      input.providerMessageId,
      input.sender,
      input.recipients,
      input.bodyText,
      input.sentAt,
      input.isUnread,
      input.direction,
    ],
  );
}

export function parseEmailList(raw: string | undefined): string[] {
  if (!raw) {
    return [];
  }

  return raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function truncate(value: string, max = 4000): string {
  if (value.length <= max) {
    return value;
  }

  return `${value.slice(0, max)}...`;
}
