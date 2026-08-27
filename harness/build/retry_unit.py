#!/usr/bin/env python3
"""접지 재시도 시뮬레이션 (#39).

검출기(check_grounding.py)가 잡은 셀만 골라, **외부 신호를 물려 1회 재생성**하면
몇 셀이 돌아오는지 잰다. 물리는 것은 DB 실측 사실이지 LLM 자기 검토가 아니다 —
Huang et al. (ICLR 2024) 의 T1 제약을 통과한다. 프롬프트 형식은 여기가 원본이고
#6 이 서버로 옮긴다.

채택 조건 (그릴링에서 확정, #6):
  ① 복구 > 0
  ② 새 위장 ok = 0 — 재생성이 "행은 나오는데 틀린" SQL 을 내면 기각 (D17 서열 1).
     집계형은 자동 확정(값 하나가 틀리면 위장), 목록형은 컬럼 선택 잡음이 있어
     후보로 열거하고 사람이 가른다 (#20 방식).
  ③ 홀드아웃에서 부호가 같을 것

  python3 harness/build/retry_unit.py logs/nl2sql-unit-dev-C0.jsonl --harness C0
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_nl2sql as rn                      # noqa: E402
import check_grounding as cg                 # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def signal_text(hits):
    """검출 근거 → 재시도 프롬프트에 물릴 외부 신호. 사실 서술 + 지시 한 줄."""
    lines = []
    for h in hits:
        if h["kind"] == "number":
            lo, hi = h["observed_range"]
            lines.append(f"{h['column']} 의 실측 값 범위는 {lo}~{hi} (만원 단위)인데 "
                         f"리터럴 {h['literal']} 이 범위 밖이다.")
        elif h["kind"] == "string":
            lines.append(f"리터럴 '{h['literal']}' 은 어느 컬럼에도 없다.")
        else:
            lines.append(f"리터럴 '{h['literal']}' 은 {h['column']} 에 없고 "
                         f"{', '.join(h['found_in'])} 에 있다.")
    return "\n".join(lines)


def retry_prompt(harness, question, sql, hits):
    return (rn.build_prompt(harness, question)
            + f"\n[직전 시도 — 실패]\n{sql}\n실행 결과 0행. 데이터베이스 실측: "
            + signal_text(hits)
            + "\n위 사실에 맞게 SELECT 문 하나를 다시 만든다.\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--harness", default=None,
                    help="기본값은 덤프 파일명에서 읽는다 (nl2sql-<set>-<harness>.jsonl)")
    ap.add_argument("--container", default="cx-pg")
    args = ap.parse_args()
    harness = args.harness or os.path.basename(args.dump).rsplit("-", 1)[1].split(".")[0]

    ranges = cg.load_ranges()
    recs = [json.loads(l) for l in open(args.dump, encoding="utf-8")]
    targets = []
    for r in recs:
        if r.get("cat") not in ("UG", "UGC") or r.get("verdict") in ("exec_error", "not_select"):
            continue
        # 운영 도달 가능 범위만 — 검출은 결과가 빈손일 때만 돈다 (A2, #6).
        # 0행(목록형 no_result)과 집계 0 한 행. 행이 온 실패(위장 가족)는 검출이
        # 원리적으로 못 보는 영역이고 #30 몫이다 — 여기서 재시도하면 안 된다.
        got0 = r.get("got_rows") == 0
        agg0 = r["verdict"] == "zero_result" and r.get("got_rows") == 1
        ctrl0 = r["cat"] == "UGC" and r["verdict"] == "match" and (
            r.get("got_rows") == 0 or "COUNT" in r["ref"].upper())
        if not (got0 or agg0 or ctrl0):
            continue
        hits = cg.detect(r["sql"], ranges)
        if hits:
            targets.append((r, hits))

    recovered = still = fake = err = 0
    human = []
    for r, hits in targets:
        sql2 = rn.extract_sql(rn.generate(retry_prompt(harness, r["q"], r["sql"], hits)))
        if not re.match(r"^\s*SELECT\b", sql2, re.I):
            err += 1; out = "재생성 실패(not_select)"
        else:
            got, e = rn.psql(sql2, args.container)
            ref, _ = rn.psql(r["ref"], args.container)
            if e:
                err += 1; out = f"실행오류 {e[:40]}"
            elif rn.normalize(got) == rn.normalize(ref):
                recovered += 1; out = "복구"
            elif rn.zero_result(got, ref):
                still += 1; out = "여전히 빈손"
            elif r["axes"]["form"] == "c":
                fake += 1; out = f"위장 확정 ({got[0][0] if got else '?'} ≠ {ref[0][0]})"
            else:
                human.append(r["id"]); out = "불일치 ← 사람 판정"
        print(f"  {r['id']:16} {r['cat']:3} {out:22} {sql2[:70]}")

    print(f"\n{os.path.basename(args.dump)} → 재시도 {len(targets)}셀: "
          f"복구 {recovered} · 여전히 빈손 {still} · 위장 확정 {fake} · "
          f"사람 판정 {len(human)} · 오류 {err}")
    if human:
        print(f"  사람 판정 후보: {', '.join(human)}")


if __name__ == "__main__":
    main()
