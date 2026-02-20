"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";

import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { reply, thread as fetchThread } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { ThreadDetail } from "@/types";

export default function ThreadPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const platform = searchParams.get("platform") ?? "email";
  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [replyBody, setReplyBody] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token || !params.id) {
      return;
    }
    setLoading(true);
    fetchThread(token, params.id, platform)
      .then(setThread)
      .catch((err) => setStatus(err instanceof Error ? err.message : "Failed to load thread"))
      .finally(() => setLoading(false));
  }, [params.id, platform]);

  const latestIncoming = useMemo(() => {
    return thread?.messages.find((message) => message.direction === "incoming");
  }, [thread]);

  const handleReply = async () => {
    if (!thread || !latestIncoming) {
      return;
    }
    const token = getToken();
    if (!token) {
      return;
    }
    try {
      await reply(token, latestIncoming.id, replyBody, platform);
      setReplyBody("");
      const refreshed = await fetchThread(token, params.id, platform);
      setThread(refreshed);
      setStatus("Reply sent successfully.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Failed to send reply");
    }
  };

  return (
    <div>
      <Topbar title="Thread View" subtitle="Read full context and send a reply." />

      {loading ? <p className="text-sm text-slate-500">Loading thread...</p> : null}
      {status ? <p className="mb-4 text-sm text-slate-600">{status}</p> : null}
      {thread ? (
        <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
          <Card>
            <CardHeader>
              <CardTitle>{thread.subject || "Conversation"}</CardTitle>
              <CardDescription>Participants: {thread.participants.join(", ") || "N/A"}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {thread.messages.map((message) => (
                <div key={message.id} className="rounded-xl border border-border bg-white p-3">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <Badge variant="secondary">{message.platform}</Badge>
                    <Badge variant={message.direction === "incoming" ? "outline" : "default"}>
                      {message.direction}
                    </Badge>
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
                  </div>
                  <p className="text-xs text-slate-500">
                    {message.sender} • {new Date(message.sent_at).toLocaleString()}
                  </p>
                  <p className="mt-2 text-sm">{message.body}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Thread Summary</CardTitle>
                <CardDescription>Phase 2 summary placeholder.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-600">
                  AI summary will appear here once summarization is enabled for this platform.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Reply</CardTitle>
                <CardDescription>Send a direct response to the latest inbound message.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Textarea
                  value={replyBody}
                  onChange={(event) => setReplyBody(event.target.value)}
                  placeholder="Type your response..."
                />
                <Button onClick={handleReply} disabled={!replyBody.trim() || !latestIncoming}>
                  Send Reply
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  );
}
