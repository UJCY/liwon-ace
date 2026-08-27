#!/usr/bin/env python3
"""병렬 짝 신호 동결 검사 — 목록 변을 축 신호가 맞게 고르는가 (#12).

인프라가 필요 없다. 도구도 LLM 도 태우지 않고 `tools.list_side_tool` 이라는
순수 함수 하나만 6문항 위에서 돌린다.

  python3 harness/build/check_pair_signal.py

**이 기대값은 합의문(docs/agreements/issue-12-parallel-pair-selection.md)의
책상 검증 표다. 측정 후 이 표를 고치는 것은 반증 성립(결정 5-1) — 고치지 말고
중단·보고한다.** 신호 오선택은 1건이라도 반증이다: 판정이 정규식과 어휘 목록으로만
정해져 실행 노이즈가 낄 자리가 없기 때문이다 (결정 5-2 의 실행 노이즈 면제는
"신호는 맞았는데 실행 확인이 죽은" 건에만 해당한다).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 합의문 책상 검증 표 6행. 왼쪽이 문항, 오른쪽이 목록 변이다
# (서술 변 `vector_search` 는 고정 멤버라 규칙이 정하지 않는다).
EXPECT = {
    "X3-01": "nl2sql",
    "X3-02": "nl2sql",
    "X4-01": "knowledge_graph",
    "X4-02": "knowledge_graph",
    "R4-01": "nl2sql",
    "OP-04": "nl2sql",
}


def main():
    edge = json.load(open(os.path.join(ROOT, "edge-set", "edge-questions.json"), encoding="utf-8"))
    qs = {x["id"]: x["q"] for x in edge}

    ok = 0
    for qid, want in EXPECT.items():
        q = qs[qid]
        got = tools.list_side_tool(q)
        mark = "✓" if got == want else "✗"
        ok += got == want
        print(f"  {qid:8} {mark}  기대 {want:15} 실제 {str(got):15} 첫 요구 «{tools.first_request(q)}»")
    print(f"짝 신호 {ok}/{len(EXPECT)}  (합의문 책상 검증 표)")

    # 경계 해석(+1) 동결. 패턴 선두의 `[가-힣]`·`고` 는 경계 표지가 아니라 첫 요구
    # 마지막 어절의 끝 음절이다 (`장애,` 의 `애`). `question[:b]` 로 자르면 `장애` 가
    # 잘려 R4-01 의 판정 어휘가 `제품` 이 된다 — 목록 변은 같지만 표와 다르다.
    boundary = "장애" in tools.first_request(qs["R4-01"])
    print(f"경계 해석  {'✓' if boundary else '✗'}  R4-01 첫 요구가 `장애` 를 담는다")

    if ok != len(EXPECT) or not boundary:
        sys.exit(1)


if __name__ == "__main__":
    main()
