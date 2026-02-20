import type { Pool } from "pg";
import { WebClient } from "@slack/web-api";
import { decryptSecret, type ConnectedAccount } from "@unified-inbox/shared";
import { truncate, upsertThreadAndMessage } from "./shared";

function parseTimestamp(ts: string): Date {
  return new Date(Math.floor(Number(ts)) * 1000);
}

export async function syncSlackAccount(pool: Pool, account: ConnectedAccount): Promise<number> {
  const token = decryptSecret(account.access_token_encrypted);
  const client = new WebClient(token);

  const conversations = await client.conversations.list({
    types: "public_channel,private_channel,im,mpim",
    exclude_archived: true,
    limit: 50,
  });

  const channels = conversations.channels ?? [];
  let processed = 0;

  for (const channel of channels) {
    if (!channel.id) {
      continue;
    }

    const history = await client.conversations.history({
      channel: channel.id,
      limit: 25,
      inclusive: true,
    });

    for (const msg of history.messages ?? []) {
      if (!msg.ts || !msg.text || msg.subtype) {
        continue;
      }

      const sender = msg.user ?? msg.username ?? "unknown";
      const sentAt = parseTimestamp(msg.ts);
      const threadTs = msg.thread_ts ?? msg.ts;
      const providerThreadId = `${channel.id}:${threadTs}`;
      const providerMessageId = `${channel.id}:${msg.ts}`;
      const channelName = channel.name ? `#${channel.name}` : channel.id;
      const channelLastRead =
        "last_read" in channel && typeof channel.last_read === "string"
          ? Number(channel.last_read)
          : 0;
      const isUnread = channelLastRead ? Number(msg.ts) > channelLastRead : true;
      const direction = sender === account.external_account_id ? "outbound" : "inbound";

      await upsertThreadAndMessage(pool, {
        userId: account.user_id,
        accountId: account.id,
        providerThreadId,
        providerMessageId,
        subject: channelName,
        sender,
        recipients: [],
        bodyText: truncate(msg.text),
        sentAt,
        isUnread,
        direction,
      });

      processed += 1;
    }
  }

  await pool.query(
    `UPDATE accounts
     SET metadata = jsonb_set(metadata, '{last_sync_at}', to_jsonb(NOW()::text), true),
         updated_at = NOW()
     WHERE id = $1`,
    [account.id],
  );

  return processed;
}
