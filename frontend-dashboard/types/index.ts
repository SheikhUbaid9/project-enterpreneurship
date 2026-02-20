export type Role = "owner" | "admin" | "member";
export type Platform = "email" | "slack" | "whatsapp";
export type Priority = "urgent" | "normal" | "low";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface Message {
  id: string;
  thread_id: string;
  user_id: string;
  platform: Platform;
  sender: string;
  recipients: string[];
  subject?: string | null;
  body: string;
  is_unread: boolean;
  direction: "incoming" | "outgoing";
  priority: Priority;
  sent_at: string;
}

export interface ThreadDetail {
  id: string;
  user_id: string;
  platform: Platform;
  subject?: string | null;
  participants: string[];
  unread_count: number;
  messages: Message[];
}

export interface PlatformStatus {
  platform: Platform;
  connected: boolean;
  status: string;
  detail?: string | null;
}
