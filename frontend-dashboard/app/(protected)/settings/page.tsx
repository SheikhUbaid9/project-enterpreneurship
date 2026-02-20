"use client";

import { useEffect, useState } from "react";

import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { me, roles, users } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import type { User } from "@/types";

export default function SettingsPage() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [availableRoles, setAvailableRoles] = useState<string[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }

    Promise.all([me(token), roles()])
      .then(([user, roleList]) => {
        setCurrentUser(user);
        setAvailableRoles(roleList);
        return user;
      })
      .then(async (user) => {
        if (user.role === "owner" || user.role === "admin") {
          const userList = await users(token);
          setAllUsers(userList);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load settings"));
  }, []);

  return (
    <div>
      <Topbar title="Settings" subtitle="RBAC view and basic environment settings." />
      {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Current User</CardTitle>
            <CardDescription>Authenticated identity and role.</CardDescription>
          </CardHeader>
          <CardContent>
            {currentUser ? (
              <div className="space-y-2 text-sm">
                <p>
                  <span className="font-medium">Email:</span> {currentUser.email}
                </p>
                <p>
                  <span className="font-medium">Role:</span>{" "}
                  <Badge variant="secondary" className="ml-1">
                    {currentUser.role}
                  </Badge>
                </p>
                <button
                  className="mt-4 rounded-lg border border-border px-3 py-2 text-xs hover:bg-muted"
                  onClick={() => {
                    clearToken();
                    window.location.href = "/login";
                  }}
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Loading user...</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Available Roles</CardTitle>
            <CardDescription>Configured RBAC roles from auth service.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {availableRoles.map((role) => (
              <Badge key={role} variant="outline">
                {role}
              </Badge>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Team Users</CardTitle>
          <CardDescription>Owner/Admin can inspect all users.</CardDescription>
        </CardHeader>
        <CardContent>
          {allUsers.length === 0 ? (
            <p className="text-sm text-slate-500">No team listing available for this role.</p>
          ) : (
            <div className="space-y-2">
              {allUsers.map((user) => (
                <div key={user.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                  <p className="text-sm">{user.email}</p>
                  <Badge variant="secondary">{user.role}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
