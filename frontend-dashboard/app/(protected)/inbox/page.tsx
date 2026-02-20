"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { unreadMessages } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Message } from "@/types";

export default function InboxPage() {
  const [platform, setPlatform] = useState("all");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }
    setLoading(true);
    unreadMessages(token, platform, 50)
      .then((data) => {
        setMessages(data);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load messages");
      })
      .finally(() => setLoading(false));
  }, [platform]);

  const grouped = useMemo(() => {
    return [...messages].sort((a, b) => new Date(b.sent_at).getTime() - new Date(a.sent_at).getTime());
  }, [messages]);

  return (
    <div>
      <Topbar title="Unified Inbox" subtitle="Monitor and reply across connected platforms." />
      <Card className="mb-4">
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="text-base">Filters</CardTitle>
          <Select value={platform} onChange={(event) => setPlatform(event.target.value)} className="w-40">
            <option value="all">All platforms</option>
            <option value="email">Email</option>
            <option value="slack">Slack</option>
            <option value="whatsapp">WhatsApp</option>
          </Select>
        </CardHeader>
      </Card>
      {error ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-red-600">{error}</p>
          </CardContent>
        </Card>
      ) : null}
      <div className="space-y-3">
        {loading ? <p className="text-sm text-slate-500">Loading messages...</p> : null}
        {!loading && grouped.length === 0 ? <p className="text-sm text-slate-500">No unread messages.</p> : null}
        {grouped.map((message) => (
          <Card key={message.id} className="transition hover:-translate-y-0.5 hover:shadow-lg">
            <CardContent className="pt-6">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Badge variant="secondary">{message.platform}</Badge>
                <Badge
                  variant={
                    message.priority === "urgent"
                      ? "urgent"
                      : message.priority === "low"
                        ? "low"
                        : "outline"
                  }
                >
                  {message.priority}
                </Badge>
                <Badge variant="outline">{message.direction}</Badge>
              </div>
              <p className="text-sm font-medium">{message.subject || "(No Subject)"}</p>
              <p className="mt-1 text-sm text-slate-600">{message.body.slice(0, 150)}</p>
              <div className="mt-4 flex items-center justify-between">
                <p className="text-xs text-slate-500">
                  {message.sender} • {new Date(message.sent_at).toLocaleString()}
                </p>
                <Link href={`/thread/${message.thread_id}?platform=${message.platform}`}>
                  <Button variant="outline" size="sm">
                    Open Thread
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
