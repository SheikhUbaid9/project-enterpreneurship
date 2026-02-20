import Fastify, { type FastifyReply, type FastifyRequest } from "fastify";
import cors from "@fastify/cors";
import jwt from "@fastify/jwt";
import { closePool, getPool } from "@unified-inbox/shared";
import { authenticate } from "./auth";
import { env } from "./config";
import { closeQueue } from "./queue";
import { authRoutes } from "./routes/auth";
import { accountRoutes } from "./routes/accounts";
import { threadRoutes } from "./routes/threads";
import { syncRoutes } from "./routes/sync";

declare module "@fastify/jwt" {
  interface FastifyJWT {
    payload: { userId: string; email: string };
    user: { userId: string; email: string };
  }
}

declare module "fastify" {
  interface FastifyInstance {
    authenticate: (request: FastifyRequest, reply: FastifyReply) => Promise<void>;
  }
}

async function buildServer() {
  const app = Fastify({ logger: true });

  app.register(cors, {
    origin: true,
  });

  app.register(jwt, {
    secret: env.JWT_SECRET,
  });

  app.decorate("authenticate", authenticate);

  app.get("/health", async () => ({ status: "ok" }));
  app.register(authRoutes, { prefix: "/auth" });
  app.register(accountRoutes, { prefix: "/accounts" });
  app.register(threadRoutes, { prefix: "/threads" });
  app.register(syncRoutes, { prefix: "/sync" });

  return app;
}

async function start() {
  getPool();

  const app = await buildServer();

  const closeSignals = ["SIGINT", "SIGTERM"] as const;
  for (const signal of closeSignals) {
    process.on(signal, async () => {
      try {
        await app.close();
        await closeQueue();
        await closePool();
      } finally {
        process.exit(0);
      }
    });
  }

  await app.listen({ port: env.PORT, host: "0.0.0.0" });
}

start().catch((error) => {
  console.error(error);
  process.exit(1);
});
