"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Inbox, Link2, MessageCircle, Settings } from "lucide-react";

import { cn } from "@/lib/utils";

const navItems = [
  { href: "/inbox", label: "Inbox", icon: Inbox },
  { href: "/platforms", label: "Platforms", icon: Link2 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-full border-b border-border bg-card p-4 md:h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="mb-6 flex items-center gap-2">
        <div className="rounded-lg bg-accent p-2 text-accentfg">
          <MessageCircle className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold">Multi-Platform Inbox</p>
          <p className="text-xs text-slate-500">MCP Dashboard</p>
        </div>
      </div>
      <nav className="flex gap-2 md:flex-col">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-colors",
                active ? "bg-accent text-accentfg" : "text-slate-700 hover:bg-muted",
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
