import type { Message, PlatformStatus, ThreadDetail, TokenResponse, User } from "@/types";

const AUTH_API = process.env.NEXT_PUBLIC_AUTH_API_URL ?? "http://localhost:8001";
const GATEWAY_API = process.env.NEXT_PUBLIC_GATEWAY_API_URL ?? "http://localhost:8000";

async function request<T>(
  baseUrl: string,
  path: string,
  init: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${baseUrl}${path}`, { ...init, headers, cache: "no-store" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }

  return (await response.json()) as T;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>(AUTH_API, "/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function me(token: string): Promise<User> {
  return request<User>(AUTH_API, "/auth/me", {}, token);
}

export async function roles(): Promise<string[]> {
  return request<string[]>(AUTH_API, "/auth/roles");
}

export async function users(token: string): Promise<User[]> {
  return request<User[]>(AUTH_API, "/auth/users", {}, token);
}

export async function unreadMessages(token: string, platform = "all", limit = 50): Promise<Message[]> {
  const payload = await request<{ messages: Message[] }>(
    GATEWAY_API,
    `/messages/unread?platform=${encodeURIComponent(platform)}&limit=${limit}`,
    {},
    token,
  );
  return payload.messages;
}

export async function thread(token: string, threadId: string, platform = "email"): Promise<ThreadDetail> {
  const payload = await request<{ thread: ThreadDetail }>(
    GATEWAY_API,
    `/threads/${threadId}?platform=${encodeURIComponent(platform)}`,
    {},
    token,
  );
  return payload.thread;
}

export async function reply(
  token: string,
  messageId: string,
  content: string,
  platform = "email",
): Promise<Message> {
  const payload = await request<{ message: Message }>(
    GATEWAY_API,
    `/messages/${messageId}/reply`,
    {
      method: "POST",
      body: JSON.stringify({ platform, content }),
    },
    token,
  );
  return payload.message;
}

export async function markRead(token: string, messageIds: string[], platform = "email"): Promise<Message[]> {
  const payload = await request<{ messages: Message[] }>(
    GATEWAY_API,
    "/messages/read",
    {
      method: "PATCH",
      body: JSON.stringify({ platform, message_ids: messageIds }),
    },
    token,
  );
  return payload.messages;
}

export async function platforms(token: string): Promise<PlatformStatus[]> {
  const payload = await request<{ platforms: PlatformStatus[] }>(GATEWAY_API, "/platforms", {}, token);
  return payload.platforms;
}
