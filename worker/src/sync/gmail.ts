import type { Pool } from "pg";
import { google, type gmail_v1 } from "googleapis";
import { decryptSecret, type ConnectedAccount } from "@unified-inbox/shared";
import { env } from "../config";
import { parseEmailList, truncate, upsertThreadAndMessage } from "./shared";

function getHeader(payload: gmail_v1.Schema$MessagePart | undefined, name: string): string | undefined {
  const headers = payload?.headers ?? [];
  const match = headers.find((header) => header.name?.toLowerCase() === name.toLowerCase());
  return match?.value ?? undefined;
}

function decodeBase64Url(value: string): string {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
  return Buffer.from(padded, "base64").toString("utf8");
}

function extractPlainText(payload: gmail_v1.Schema$MessagePart | undefined): string {
  if (!payload) {
    return "";
  }

  if (payload.mimeType === "text/plain" && payload.body?.data) {
    return decodeBase64Url(payload.body.data);
  }

  for (const part of payload.parts ?? []) {
    const text = extractPlainText(part);
    if (text) {
      return text;
    }
  }

  if (payload.body?.data) {
    return decodeBase64Url(payload.body.data);
  }

  return "";
}

export async function syncGmailAccount(pool: Pool, account: ConnectedAccount): Promise<number> {
  if (!env.GMAIL_CLIENT_ID || !env.GMAIL_CLIENT_SECRET) {
    throw new Error("GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET are required for Gmail sync");
  }

  const oauth2Client = new google.auth.OAuth2(env.GMAIL_CLIENT_ID, env.GMAIL_CLIENT_SECRET);
  oauth2Client.setCredentials({
    access_token: decryptSecret(account.access_token_encrypted),
    refresh_token: account.refresh_token_encrypted ? decryptSecret(account.refresh_token_encrypted) : undefined,
  });

  const gmail = google.gmail({ version: "v1", auth: oauth2Client });

  const listResponse = await gmail.users.messages.list({
    userId: "me",
    maxResults: env.SYNC_BATCH_SIZE,
    q: "in:inbox newer_than:14d",
  });

  const messageRefs = listResponse.data.messages ?? [];
  let processed = 0;

  for (const ref of messageRefs) {
    if (!ref.id) {
      continue;
    }

    const messageResponse = await gmail.users.messages.get({
      userId: "me",
      id: ref.id,
      format: "full",
    });

    const message = messageResponse.data;
    const payload = message.payload;

    const subject = getHeader(payload, "subject") ?? null;
    const sender = getHeader(payload, "from") ?? "unknown";
    const recipients = parseEmailList(getHeader(payload, "to"));
    const sentAtCandidate = message.internalDate
      ? new Date(Number(message.internalDate))
      : new Date(getHeader(payload, "date") ?? Date.now());
    const sentAt = Number.isNaN(sentAtCandidate.getTime()) ? new Date() : sentAtCandidate;

    const bodyText = truncate(extractPlainText(payload) || "(empty message)");
    const isUnread = (message.labelIds ?? []).includes("UNREAD");

    await upsertThreadAndMessage(pool, {
      userId: account.user_id,
      accountId: account.id,
      providerThreadId: message.threadId ?? message.id ?? ref.id,
      providerMessageId: message.id ?? ref.id,
      subject,
      sender,
      recipients,
      bodyText,
      sentAt,
      isUnread,
      direction: "inbound",
    });

    processed += 1;
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
