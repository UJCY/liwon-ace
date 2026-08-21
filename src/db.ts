/** PostgreSQL 연결. 모든 도구가 여기로 향한다 (과제 흐름도). */
import pg from "pg";

export const pool = new pg.Pool({
  host: process.env["PGHOST"] ?? "localhost",
  port: Number(process.env["PGPORT"] ?? 55432),
  user: process.env["PGUSER"] ?? "postgres",
  password: process.env["PGPASSWORD"] ?? "cx",
  database: process.env["PGDATABASE"] ?? "companyx",
  max: 4,
});

export async function query<T extends pg.QueryResultRow = pg.QueryResultRow>(
  sql: string,
  params: unknown[] = [],
): Promise<T[]> {
  const r = await pool.query<T>(sql, params);
  return r.rows;
}

/** pgvector 리터럴. 파라미터 바인딩이 vector 타입을 안 받으므로 문자열로 만든다. */
export const toVector = (v: number[]) => `[${v.map((x) => x.toFixed(6)).join(",")}]`;
