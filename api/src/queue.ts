import { Queue } from "bullmq";
import { QUEUE_NAMES, type AccountSyncJob, type AccountSyncJobName } from "@unified-inbox/shared";
import { env } from "./config";

function getRedisConnection(redisUrl: string) {
  const parsed = new URL(redisUrl);
  const dbSegment = parsed.pathname.replace(/^\//, "");
  const db = dbSegment ? Number.parseInt(dbSegment, 10) : undefined;

  if (dbSegment && Number.isNaN(db)) {
    throw new Error("REDIS_URL database index must be numeric");
  }

  return {
    host: parsed.hostname,
    port: parsed.port ? Number.parseInt(parsed.port, 10) : 6379,
    username: parsed.username || undefined,
    password: parsed.password || undefined,
    db,
    maxRetriesPerRequest: null,
  };
}

const connection = getRedisConnection(env.REDIS_URL);

export const accountSyncQueue = new Queue<AccountSyncJob, void, AccountSyncJobName>(QUEUE_NAMES.ACCOUNT_SYNC, {
  connection,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: "exponential",
      delay: 1000,
    },
    removeOnComplete: 100,
    removeOnFail: 500,
  },
});

export async function closeQueue(): Promise<void> {
  await accountSyncQueue.close();
}
