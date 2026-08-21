/** 개체 식별 — 등록된 것과 등록되지 않은 언급을 나눈다. */
import { query } from "../db.js";
import { companySuffix, idPrefixes } from "../assets.js";

export interface NodeRef { id: string; type: string; name: string }

let nodeCache: NodeRef[] | null = null;

async function allNodes(): Promise<NodeRef[]> {
  if (!nodeCache) nodeCache = await query<NodeRef>("SELECT id, type, name FROM nodes");
  return nodeCache;
}

const ID_RE = new RegExp(`(?:${idPrefixes.join("|")})[- ]?[A-Za-z0-9]+`, "gi");
const KO_RE = new RegExp(`[가-힣]{2,5}(?:${companySuffix.join("|")})`, "g");

export async function findEntities(question: string): Promise<{
  matched: NodeRef[];
  unmatched: string[];
}> {
  const nodes = await allNodes();
  const names = new Set(nodes.map((n) => n.name));
  let matched = nodes.filter((n) => n.name && question.includes(n.name));

  const unmatched: string[] = [];
  for (const re of [ID_RE, KO_RE]) {
    re.lastIndex = 0;
    for (const m of question.matchAll(re)) {
      if (!names.has(m[0])) unmatched.push(m[0]);
    }
  }
  // 미등록 언급이 등록 이름을 **포함**하면 그 등록 이름은 우연한 부분문자열이다.
  // "Client-ZZ" 안의 "Client-Z" — 개체 부재(T5)를 부분 매칭이 가리면 안 된다.
  if (unmatched.length) {
    matched = matched.filter(
      (e) => !unmatched.some((u) => u !== e.name && u.includes(e.name)),
    );
  }
  return { matched, unmatched: [...new Set(unmatched)] };
}
