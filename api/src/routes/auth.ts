import type { FastifyInstance } from "fastify";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { getPool } from "@unified-inbox/shared";

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(128),
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(128),
});

export async function authRoutes(fastify: FastifyInstance): Promise<void> {
  const pool = getPool();

  fastify.post("/register", async (request, reply) => {
    const body = registerSchema.parse(request.body);
    const email = body.email.toLowerCase().trim();

    const existing = await pool.query("SELECT id FROM users WHERE email = $1", [email]);
    if (existing.rowCount) {
      return reply.code(409).send({ error: "User already exists" });
    }

    const passwordHash = await bcrypt.hash(body.password, 12);

    const result = await pool.query(
      `INSERT INTO users (email, password_hash)
       VALUES ($1, $2)
       RETURNING id, email, created_at`,
      [email, passwordHash],
    );

    const user = result.rows[0] as { id: string; email: string; created_at: string };
    const token = fastify.jwt.sign({ userId: user.id, email: user.email }, { expiresIn: "7d" });

    return reply.code(201).send({
      token,
      user,
    });
  });

  fastify.post("/login", async (request, reply) => {
    const body = loginSchema.parse(request.body);
    const email = body.email.toLowerCase().trim();

    const result = await pool.query(
      `SELECT id, email, password_hash
       FROM users
       WHERE email = $1`,
      [email],
    );

    if (!result.rowCount) {
      return reply.code(401).send({ error: "Invalid credentials" });
    }

    const user = result.rows[0] as { id: string; email: string; password_hash: string };
    const isValid = await bcrypt.compare(body.password, user.password_hash);
    if (!isValid) {
      return reply.code(401).send({ error: "Invalid credentials" });
    }

    const token = fastify.jwt.sign({ userId: user.id, email: user.email }, { expiresIn: "7d" });

    return reply.send({
      token,
      user: { id: user.id, email: user.email },
    });
  });

  fastify.get("/me", { preHandler: [fastify.authenticate] }, async (request) => {
    const userId = request.user.userId;
    const result = await pool.query(
      `SELECT id, email, created_at
       FROM users
       WHERE id = $1`,
      [userId],
    );

    if (!result.rowCount) {
      return { user: null };
    }

    return { user: result.rows[0] };
  });
}
