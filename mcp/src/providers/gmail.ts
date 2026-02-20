import { google } from "googleapis";
import { decryptSecret } from "@unified-inbox/shared";

export interface GmailReplyInput {
  accessTokenEncrypted: string;
  refreshTokenEncrypted: string | null;
  threadProviderId: string;
  recipient: string;
  subject: string | null;
  body: string;
  inReplyToProviderMessageId?: string | null;
  gmailClientId: string;
  gmailClientSecret: string;
}

export async function sendGmailReply(input: GmailReplyInput): Promise<string> {
  if (!input.gmailClientId || !input.gmailClientSecret) {
    throw new Error("GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET are required for Gmail reply");
  }

  if (!input.recipient) {
    throw new Error("No recipient available for Gmail reply");
  }

  const oauth2Client = new google.auth.OAuth2(input.gmailClientId, input.gmailClientSecret);
  oauth2Client.setCredentials({
    access_token: decryptSecret(input.accessTokenEncrypted),
    refresh_token: input.refreshTokenEncrypted ? decryptSecret(input.refreshTokenEncrypted) : undefined,
  });

  const gmail = google.gmail({ version: "v1", auth: oauth2Client });

  const subject = input.subject?.toLowerCase().startsWith("re:")
    ? input.subject
    : `Re: ${input.subject ?? "No Subject"}`;

  const headers = [
    `To: ${input.recipient}`,
    `Subject: ${subject}`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=UTF-8",
  ];

  if (input.inReplyToProviderMessageId) {
    headers.push(`In-Reply-To: <${input.inReplyToProviderMessageId}>`);
    headers.push(`References: <${input.inReplyToProviderMessageId}>`);
  }

  const mimeMessage = `${headers.join("\r\n")}\r\n\r\n${input.body}`;
  const raw = Buffer.from(mimeMessage).toString("base64url");

  const response = await gmail.users.messages.send({
    userId: "me",
    requestBody: {
      raw,
      threadId: input.threadProviderId,
    },
  });

  if (!response.data.id) {
    throw new Error("Gmail reply failed: no provider message id returned");
  }

  return response.data.id;
}
