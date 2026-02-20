import pino from "pino";
import { Queue, Worker } from "bullmq";
import {
  ACCOUNT_SYNC_JOB_NAMES,
  closePool,
  getPool,
  QUEUE_NAMES,
  type AccountSyncJob,
  type AccountSyncJobName,
  type ConnectedAccount,
} from "@unified-inbox/shared";
import { env } from "./config";
import { syncGmailAccount } from "./sync/gmail";
import { syncSlackAccount } from "./sync/slack";

const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  transport:
    process.env.NODE_ENV === "development"
      ? {
          target: "pino-pretty",
          options: {
            colorize: true,
          },
        }
      : undefined,
});

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

const accountSyncQueue = new Queue<AccountSyncJob, void, AccountSyncJobName>(QUEUE_NAMES.ACCOUNT_SYNC, {
  connection,
});

async function loadAccounts(job: AccountSyncJob): Promise<ConnectedAccount[]> {
  const pool = getPool();

  if (job.accountId) {
    const query = await pool.query(
      `SELECT id, user_id, provider, external_account_id, access_token_encrypted, refresh_token_encrypted, token_expires_at, metadata
       FROM accounts
       WHERE id = $1
         AND user_id = $2`,
      [job.accountId, job.userId],
    );

    return query.rows as ConnectedAccount[];
  }

  const query = await pool.query(
    `SELECT id, user_id, provider, external_account_id, access_token_encrypted, refresh_token_encrypted, token_expires_at, metadata
     FROM accounts
     WHERE user_id = $1`,
    [job.userId],
  );

  return query.rows as ConnectedAccount[];
}

async function processSyncJob(data: AccountSyncJob): Promise<void> {
  const pool = getPool();
  const accounts = await loadAccounts(data);

  logger.info({ userId: data.userId, accountCount: accounts.length }, "starting sync job");

  for (const account of accounts) {
    try {
      if (account.provider === "gmail") {
        const count = await syncGmailAccount(pool, account);
        logger.info({ accountId: account.id, provider: account.provider, count }, "gmail sync completed");
        continue;
      }

      if (account.provider === "slack") {
        const count = await syncSlackAccount(pool, account);
        logger.info({ accountId: account.id, provider: account.provider, count }, "slack sync completed");
      }
    } catch (error) {
      logger.error({ accountId: account.id, err: error }, "account sync failed");
    }
  }
}

async function start(): Promise<void> {
  getPool();

  const enqueueScheduledSweep = async () => {
    await accountSyncQueue.add(
      ACCOUNT_SYNC_JOB_NAMES.SCHEDULED,
      {
        userId: "00000000-0000-0000-0000-000000000000",
        reason: "scheduled",
      },
      {
        removeOnComplete: 20,
        removeOnFail: 20,
      },
    );
  };

  await enqueueScheduledSweep();
  const scheduleTimer = setInterval(() => {
    enqueueScheduledSweep().catch((error) => {
      logger.error({ err: error }, "failed to enqueue scheduled sync");
    });
  }, env.SYNC_SCHEDULE_SECONDS * 1000);
  scheduleTimer.unref();

  const worker = new Worker<AccountSyncJob, void, AccountSyncJobName>(
    QUEUE_NAMES.ACCOUNT_SYNC,
    async (job) => {
      if (job.data.userId === "00000000-0000-0000-0000-000000000000") {
        const pool = getPool();
        const users = await pool.query("SELECT id FROM users");

        for (const user of users.rows as Array<{ id: string }>) {
          await processSyncJob({ userId: user.id, reason: "scheduled" });
        }

        return;
      }

      await processSyncJob(job.data);
    },
    {
      connection,
      concurrency: 5,
    },
  );

  worker.on("ready", () => {
    logger.info("worker is ready");
  });

  worker.on("failed", (job, err) => {
    logger.error({ jobId: job?.id, err }, "job failed");
  });

  const shutdown = async () => {
    logger.info("shutting down worker");
    await worker.close();
    await accountSyncQueue.close();
    await closePool();
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

start().catch((error) => {
  logger.error({ err: error }, "worker startup failed");
  process.exit(1);
});
