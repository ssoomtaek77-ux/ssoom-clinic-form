import json
import textwrap
import streamlit as st
import google.generativeai as genai
from typing import Dict, Any, List

# -----------------------------
# 0) 시크릿에서 API 키 읽기 (이전 방식 유지)
# -----------------------------
def _read_api_key() -> str:
    # 권장: [general] GOOGLE_API_KEY
    try:
        return st.secrets["general"]["GOOGLE_API_KEY"]
    except Exception:
        # 포올백: GOOGLE_API_KEY 단독 키
        try:
            return st.secrets["GOOGLE_API_KEY"]
        except Exception:
            return ""

API_KEY = _read_api_key()
if not API_KEY:
    st.error("⚠️ Streamlit secrets에 [general] 섹션의 GOOGLE_API_KEY 를 넣어주세요.")
    st.stop()

# Google AI 설정
genai.configure(api_key=API_KEY)
MODEL = "gemini-1.5-flash"

# -----------------------------
# 1) 고정 옵션 정의 (AI가 이 범위 내에서만 추천)
# -----------------------------
SYMPTOMS = ["머리","허리","어깨","발/목/뒤꿈치","무릎","손목","허벅지","뒷목 어깻죽지","등","손","손가락",
            "엉덩이/골반","팔꿈치","장단지","손/팔 저림","두통/어지러움","설사","생리통","다리 감각 이상",
            "변비","소화불량","불안 장애","불면","알레르지질환"]

CAUSES = ["사고(운동)","사고(교통사고)","사고(상해)","사고(일상생활)","음식","스트레스","원인모름","기존질환","생활습관 및 환경"]

CLASSIFICATIONS = ["급성질환(10~14일)", "만성질환(15일~3개월 이내)", "웰니스(3개월 이상)"]
CLS_CANON = {"급성": CLASSIFICATIONS[0], "만성": CLASSIFICATIONS[1], "웰니스": CLASSIFICATIONS[2]}

DURATIONS = ["1주","2주","3주","4주","1개월 이상"]

COVERED = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
UNCOVERED = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]

# -----------------------------
# 2) 유틸: 모델 호출/JSON 파싱/복사버튼
# -----------------------------
def call_gemini(prompt: str) -> Dict[str, Any]:
    """Gemini 호출 → dict로 결과 반환. 실패 시 {'error': '...'}"""
    try:
        model = genai.GenerativeModel(MODEL)
        res = model.generate_content(prompt)
        text = getattr(res, "text", "") or ""
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}

def safe_json_from_text(text: str):
    """응답에서 JSON만 안전 추출."""
    try:
        m = None
        # 백틱으로 감싼 경우 대응
        if "```" in text:
            chunks = text.split("```")
            # ```json ... ``` 구간 우선 탐색
            for i in range(0, len(chunks)-1):
                if chunks[i].strip().lower().endswith("json"):
                    m = chunks[i+1]
                    break
            if not m:
                # 그냥 첫 코드블럭
                m = chunks[1]
            return json.loads(m)
        # 중괄호 매칭
        import re
        m2 = re.search(r"\{[\s\S]*\}$", text.strip())
        payload = m2.group(0) if m2 else text
        return json.loads(payload)
    except Exception:
        return None

def copy_button(label: str, text: str, key: str):
    """클립보드 복사 버튼 (프론트에서 실행)"""
    # Streamlit에서 클립보드 접근은 JS로 처리
    from streamlit.components.v1 import html
    safe = json.dumps(text)  # JS 문자열로 안전 변환
    html(
        f"""
        <button onclick='navigator.clipboard.writeText({safe})'
                style="padding:8px 12px;border:1px solid #ddd;border-radius:8px;cursor:pointer;">
            {label}
        </button>
        """,
        height=40,
        key=key
    )

# -----------------------------
# 3) 페이지 타이틀
# -----------------------------
st.set_page_config(page_title="일반 질환 기초 문진표", layout="wide")
st.title("일반 질환 기초 문진표")
st.caption("※ 본 출력은 참고용이며, 진단/처방이 아니고 최종 결정은 의료진의 임상 판단에 따릅니다.")

# -----------------------------
# 4) 입력 영역 (폼에 가두지 않음 → 섹션 항상 보임)
# -----------------------------
colA, colB = st.columns(2)
with colA:
    st.subheader("환자 기본정보")
    name = st.text_input("이름", "")
    age = st.number_input("나이", min_value=0, max_value=120, value=30)
with colB:
    bp = st.text_input("혈압/맥박", "예) 120/80, 맥박 72회")

st.subheader("1) 현재 불편한 증상")
symptoms = st.multiselect("체크 + 필요시 아래에 직접 입력", SYMPTOMS)
symptom_etc = st.text_input("기타 증상 (선택)")

st.subheader("2) 증상 시작 시점")
onset = st.selectbox("선택", ["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"])
onset_date = st.text_input("발병일(선택, 예: 2025-09-21)")

st.subheader("3) 증상 원인")
causes = st.multiselect("체크 + 필요시 아래에 직접 입력", CAUSES)
cause_etc = st.text_input("기타 원인 (선택)")

st.subheader("4) 과거 병력/복용 중 약물/현재 치료")
history = st.text_area("예: 아토피약 복용중 / 항히스타민제 복용중 / 물리치료 주 1회 등")

st.subheader("5) 내원 빈도")
visit = st.selectbox("선택", ["매일 통원","주 3~6회","주 1~2회","기타"])
visit_etc = st.text_input("기타 선택 시 구체적으로 (선택)")

# 입력 데이터 합치기
sym_all = symptoms[:] + ([symptom_etc] if symptom_etc.strip() else [])
cause_all = causes[:] + ([cause_etc] if cause_etc.strip() else [])
visit_final = f"기타({visit_etc})" if visit == "기타" and visit_etc.strip() else visit

patient_dict = {
    "name": name.strip(),
    "age": age,
    "bp": bp.strip(),
    "symptoms": sym_all,
    "onset": onset,
    "onset_date": onset_date.strip(),
    "causes": cause_all,
    "history": history.strip(),
    "visit": visit_final
}

# -----------------------------
# 5) 문진 요약
# -----------------------------
st.markdown("---")
st.subheader("📝 문진 요약")

summary_prompt = textwrap.dedent(f"""
너는 숨쉬는한의원 내부 상담 도우미다.
아래 환자 문진을 간결하고 보기 좋게 정리해라.
진단/처방/평가적 표현 금지. 입력값만 재구성.

[환자 문진]
- 이름/나이: {patient_dict['name'] or '-'} / {patient_dict['age']}
- 혈압/맥박: {patient_dict['bp'] or '-'}
- 주요 증상: {', '.join(patient_dict['symptoms']) if patient_dict['symptoms'] else '-'}
- 증상 시작: {patient_dict['onset']}{' ('+patient_dict['onset_date']+')' if patient_dict['onset_date'] else ''}
- 원인: {', '.join(patient_dict['causes']) if patient_dict['causes'] else '-'}
- 과거 병력/복용약/현재 치료: {patient_dict['history'] or '-'}
- 내원 빈도: {patient_dict['visit'] or '-'}
""").strip()

c1, c2 = st.columns([1,1])
with c1:
    if st.button("① 요약 생성"):
        r = call_gemini(summary_prompt)
        st.session_state["summary_text"] = r.get("text") or f"❌ 오류: {r.get('error','생성 실패')}"
with c2:
    if st.button("요약 초기화"):
        st.session_state.pop("summary_text", None)

summary_text = st.session_state.get("summary_text", "아직 생성하지 않았습니다.")
st.text_area("요약 결과", summary_text, height=180)
copy_button("요약 복사", summary_text, key="copy_sum")

# -----------------------------
# 6) AI 제안 (분류/기간/급여/비급여/주의)
#    → 지정 리스트 안에서만 추천하도록 강제
# -----------------------------
st.markdown("---")
st.subheader("🤖 AI 제안 (분류/치료/기간/주의사항)")

guardrails = textwrap.dedent(f"""
규칙:
1) 반드시 아래 선택지 내부에서만 고른다. 새로운 항목 생성 금지.
2) 필드가 비어선 안 된다(불확실하면 '가능성' 형태라도 채운다).
3) 과거 병력/약물이 모호(ex. '아토피약')하면 '추정:'으로 기재하고 병행 주의점을 쓴다.
4) JSON만 출력. 추가 설명 금지.

선택지:
- classification: ["급성","만성","웰니스"] 중 택1
- duration: {DURATIONS}
- covered(급여): {COVERED}
- uncovered(비급여): {UNCOVERED}
""").strip()

ai_prompt = textwrap.dedent(f"""
너는 숨쉬는한의원 내부 상담 보조 도구다.
아래 환자 문진을 보고 JSON만 출력하라.

필수 필드:
- classification: "급성"|"만성"|"웰니스"
- duration: {DURATIONS} 중 택1
- covered: {COVERED} 중 일부 (없으면 [])
- uncovered: {UNCOVERED} 중 일부 (없으면 [])
- rationale: 권장 근거(간결)
- objective_comment: 생활습관/재발예방 등 객관 코멘트
- caution: 병력/복용약 기반 병행 주의사항(모호하면 '추정:'을 붙여 명시)

{guardrails}

[환자 문진(JSON)]
{json.dumps(patient_dict, ensure_ascii=False, indent=2)}
""").strip()

c3, c4 = st.columns([1,1])
with c3:
    if st.button("② AI 제안 생성"):
        r = call_gemini(ai_prompt)
        if "error" in r:
            st.session_state["ai_raw"] = f"❌ 오류: {r['error']}"
            st.session_state["ai_struct"] = None
        else:
            raw = r.get("text","")
            parsed = safe_json_from_text(raw)
            if isinstance(parsed, dict):
                st.session_state["ai_struct"] = parsed
                st.session_state["ai_raw"] = ""
            else:
                st.session_state["ai_struct"] = None
                st.session_state["ai_raw"] = raw or "(JSON 파싱 실패)"
with c4:
    if st.button("AI 제안 초기화"):
        st.session_state.pop("ai_struct", None)
        st.session_state.pop("ai_raw", None)

ai_struct = st.session_state.get("ai_struct")
ai_raw = st.session_state.get("ai_raw", "")

if ai_struct:
    # 정제 & 표준 라벨 적용
    cls_short = ai_struct.get("classification","").strip()
    cls_label = CLS_CANON.get(cls_short, cls_short) or "-"
    dur = ai_struct.get("duration", "-")
    cov = [x for x in ai_struct.get("covered", []) if x in COVERED]
    unc = [x for x in ai_struct.get("uncovered", []) if x in UNCOvERED] if False else [x for x in ai_struct.get("uncovered", []) if x in UNCOVERED]
    rationale = ai_struct.get("rationale","-").strip() or "-"
    obj = ai_struct.get("objective_comment","-").strip() or "-"
    caution = ai_struct.get("caution","-").strip() or "-"

    ai_view = "\n".join([
        "📌 Gemini 제안",
        f"- 분류: {cls_label} (원본: {cls_short or '-'})",
        f"- 권장 기간: {dur}",
        f"- 급여 후보: {', '.join(cov) if cov else '-'}",
        f"- 비급여 후보: {', '.join(unc) if unc else '-'}",
        "",
        f"근거: {rationale}",
        f"📝 객관 코멘트: {obj}",
        f"⚠️ 주의사항: {caution}",
    ])
    st.text_area("AI 제안 결과", ai_view, height=220)
    copy_button("AI 제안 복사", ai_view, key="copy_ai")
elif ai_raw:
    st.text_area("AI 원문(파싱 실패 시 표시)", ai_raw, height=220)
    copy_button("AI 원문 복사", ai_raw, key="copy_ai_raw")
else:
    st.info("아직 생성하지 않았습니다.")

# -----------------------------
# 7) 최종 치료계획 (의료진 확정) + 결과 합본
# -----------------------------
st.markdown("---")
st.subheader("✅ 최종 치료계획 (의료진 확정)")

col1, col2 = st.columns(2)
with col1:
    cls_final = st.selectbox("질환 분류(의료진 확정)", CLASSIFICATIONS, index=0)
    period_final = st.selectbox("치료 기간(의료진 확정)", DURATIONS, index=0)
with col2:
    covered_sel = st.multiselect("치료 항목(급여, 의료진 선택)", COVERED)
    uncovered_sel = st.multiselect("치료 항목(비급여, 의료진 선택)", UNCOVERED)
    herb_month = st.radio("비급여 맞춤 한약 기간", ["선택 안 함","1개월","2개월","3개월"], index=0)

# 합본 만들기
summary_out = st.session_state.get("summary_text","(요약 미생성)")
ai_struct = st.session_state.get("ai_struct")
if ai_struct:
    cls_short = ai_struct.get("classification","").strip()
    cls_label = CLS_CANON.get(cls_short, cls_short) or "-"
    dur = ai_struct.get("duration","-")
    cov = [x for x in ai_struct.get("covered", []) if x in COVERED]
    unc = [x for x in ai_struct.get("uncovered", []) if x in UNCOVERED]
    rationale = ai_struct.get("rationale","-").strip() or "-"
    obj = ai_struct.get("objective_comment","-").strip() or "-"
    caution = ai_struct.get("caution","-").strip() or "-"
    ai_block = "\n".join([
        "=== Gemini 제안(참고) ===",
        f"- 분류: {cls_label} (원본: {cls_short or '-'})",
        f"- 기간: {dur}",
        f"- 급여 후보: {', '.join(cov) if cov else '-'}",
        f"- 비급여 후보: {', '.join(unc) if unc else '-'}",
        f"근거: {rationale}",
        f"📝 객관 코멘트: {obj}",
        f"⚠️ 주의사항: {caution}",
    ])
else:
    ai_block = "=== Gemini 제안(참고) ===\n(AI 제안 없음)"

manual_cov = covered_sel[:]
manual_unc = uncovered_sel[:]
if herb_month != "선택 안 함":
    # 비급여 맞춤 한약(기간) 표기
    # 중복 방지
    label = f"비급여 맞춤 한약({herb_month})"
    # '비급여 맞춤 한약'을 선택했다면 기간치환
    replaced = False
    for i, v in enumerate(manual_unc):
        if v == "비급여 맞춤 한약":
            manual_unc[i] = label
            replaced = True
            break
    if not replaced:
        manual_unc.append(label)

final_text = "\n".join([
    "=== 환자 문진 요약 ===",
    summary_out.strip(),
    "",
    ai_block,
    "",
    "=== 최종 치료계획 (의료진 확정) ===",
    f"- 분류: {cls_final}" + (f" (AI: {CLS_CANON.get(cls_short, cls_short)})" if st.session_state.get("ai_struct") else ""),
    f"- 기간: {period_final}" + (f" (AI: {dur})" if st.session_state.get("ai_struct") else ""),
    f"- 급여: {', '.join(manual_cov) if manual_cov else '-'}" + (
        f" (AI 후보: {', '.join(cov)})" if st.session_state.get("ai_struct") and cov else ""
    ),
    f"- 비급여: {', '.join(manual_unc) if manual_unc else '-'}" + (
        f" (AI 후보: {', '.join(unc)})" if st.session_state.get("ai_struct") and unc else ""
    ),
    "",
    "※ 고지: 본 계획은 의료진의 임상 판단과 환자 동의에 따라 확정되었으며, AI 출력은 참고자료로만 활용되었습니다."
])

st.text_area("최종 결과 (복사하여 EMR/문서에 붙여넣기)", final_text, height=260)
copy_button("최종 결과 복사", final_text, key="copy_final")

# 디버그(선택)
with st.expander("환경/디버그"):
    st.write({"model": MODEL, "has_api": bool(API_KEY)})
