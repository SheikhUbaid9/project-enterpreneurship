import { WebClient } from "@slack/web-api";
import { decryptSecret } from "@unified-inbox/shared";

export interface SlackReplyInput {
  accessTokenEncrypted: string;
  providerThreadId: string;
  body: string;
}

export async function sendSlackReply(input: SlackReplyInput): Promise<string> {
  const token = decryptSecret(input.accessTokenEncrypted);
  const client = new WebClient(token);

  const [channelId, threadTs] = input.providerThreadId.split(":", 2);
  if (!channelId) {
    throw new Error("Invalid Slack provider_thread_id");
  }

  const response = await client.chat.postMessage({
    channel: channelId,
    text: input.body,
    thread_ts: threadTs || undefined,
  });

  if (!response.ok || !response.ts) {
    throw new Error(`Slack reply failed: ${response.error ?? "unknown error"}`);
  }

  return `${channelId}:${response.ts}`;
}
