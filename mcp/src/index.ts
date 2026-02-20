import Fastify from "fastify";
import pino from "pino";
import { closePool, getPool } from "@unified-inbox/shared";
import { env } from "./config";
import {
  getToolDefinitions,
  getUnreadMessages,
  sendReply,
  summarizeThreads,
} from "./tools";

interface JsonRpcRequest {
  jsonrpc: "2.0";
  id?: string | number | null;
  method: string;
  params?: Record<string, unknown>;
}

interface JsonRpcError {
  code: number;
  message: string;
  data?: unknown;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  id: string | number | null;
  result?: unknown;
  error?: JsonRpcError;
}

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

function ok(id: string | number | null, result: unknown): JsonRpcResponse {
  return {
    jsonrpc: "2.0",
    id,
    result,
  };
}

function fail(id: string | number | null, code: number, message: string, data?: unknown): JsonRpcResponse {
  return {
    jsonrpc: "2.0",
    id,
    error: {
      code,
      message,
      data,
    },
  };
}

async function handleToolCall(name: string, args: Record<string, unknown> | undefined): Promise<unknown> {
  switch (name) {
    case "get_unread_messages": {
      return getUnreadMessages(args ?? {});
    }
    case "summarize_threads": {
      return summarizeThreads(args ?? {});
    }
    case "send_reply": {
      return sendReply(args ?? {});
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function buildServer() {
  const app = Fastify({ logger: false });

  app.get("/health", async () => ({ status: "ok" }));

  app.post("/mcp", async (request, reply) => {
    if (env.MCP_AUTH_TOKEN) {
      const authHeader = request.headers.authorization;
      const token = authHeader?.startsWith("Bearer ") ? authHeader.slice(7) : "";

      if (token !== env.MCP_AUTH_TOKEN) {
        return reply.code(401).send({ error: "Unauthorized" });
      }
    }

    const payload = request.body as JsonRpcRequest;
    if (!payload || payload.jsonrpc !== "2.0" || typeof payload.method !== "string") {
      return reply.code(400).send(fail(null, -32600, "Invalid Request"));
    }

    const id = payload.id ?? null;

    try {
      switch (payload.method) {
        case "initialize": {
          return reply.send(
            ok(id, {
              protocolVersion: "2025-06-18",
              serverInfo: {
                name: "Unified Inbox MCP Server",
                version: "0.1.0",
              },
              capabilities: {
                tools: {},
              },
            }),
          );
        }
        case "tools/list": {
          return reply.send(ok(id, { tools: getToolDefinitions() }));
        }
        case "tools/call": {
          const name = payload.params?.name;
          const args = payload.params?.arguments as Record<string, unknown> | undefined;

          if (typeof name !== "string") {
            return reply.send(fail(id, -32602, "Invalid params: tool name is required"));
          }

          const result = await handleToolCall(name, args);

          return reply.send(
            ok(id, {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(result, null, 2),
                },
              ],
              structuredContent: result,
            }),
          );
        }
        case "ping": {
          return reply.send(ok(id, {}));
        }
        default:
          return reply.send(fail(id, -32601, "Method not found"));
      }
    } catch (error) {
      logger.error({ err: error }, "mcp request failed");
      return reply.send(
        fail(id, -32000, "Tool execution failed", {
          message: error instanceof Error ? error.message : "Unknown error",
        }),
      );
    }
  });

  return app;
}

async function start(): Promise<void> {
  getPool();

  const app = await buildServer();
  await app.listen({ host: "0.0.0.0", port: env.MCP_PORT });

  const shutdown = async () => {
    logger.info("shutting down mcp server");
    await app.close();
    await closePool();
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

start().catch((error) => {
  logger.error({ err: error }, "mcp startup failed");
  process.exit(1);
});
