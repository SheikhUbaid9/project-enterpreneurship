export const QUEUE_NAMES = {
  ACCOUNT_SYNC: "account_sync",
} as const;

export const ACCOUNT_SYNC_JOB_NAMES = {
  MANUAL: "sync-account",
  SCHEDULED: "scheduled-sync",
} as const;

export type AccountSyncJobName =
  (typeof ACCOUNT_SYNC_JOB_NAMES)[keyof typeof ACCOUNT_SYNC_JOB_NAMES];
