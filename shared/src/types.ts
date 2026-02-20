export type Provider = "gmail" | "slack";

export interface AccountSyncJob {
  userId: string;
  accountId?: string;
  reason?: "manual" | "scheduled";
}

export interface ConnectedAccount {
  id: string;
  user_id: string;
  provider: Provider;
  external_account_id: string;
  access_token_encrypted: string;
  refresh_token_encrypted: string | null;
  token_expires_at: Date | null;
  metadata: Record<string, unknown>;
}

export type ToolCallStatus = "success" | "error";
