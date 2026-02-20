"use client";

import { useEffect, useState } from "react";

import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { platforms as fetchPlatforms } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { PlatformStatus } from "@/types";

export default function PlatformsPage() {
  const [items, setItems] = useState<PlatformStatus[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }
    fetchPlatforms(token)
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load platforms"));
  }, []);

  return (
    <div>
      <Topbar title="Platform Connections" subtitle="Monitor health and connectivity for each adapter." />
      {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item, index) => (
          <Card key={`${item.platform}-${index}`}>
            <CardHeader>
              <CardTitle className="capitalize">{item.platform}</CardTitle>
              <CardDescription>{item.detail || "No details provided."}</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <Badge variant={item.connected ? "default" : "outline"}>
                {item.connected ? "Connected" : "Disconnected"}
              </Badge>
              <Badge variant="secondary">{item.status}</Badge>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
