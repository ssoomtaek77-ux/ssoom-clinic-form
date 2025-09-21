import os
import json
import requests
import streamlit as st

# ================================
# 환경변수: GOOGLE_API_KEY 우선 사용
# ================================
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-1.5-pro"  # 🔑 올바른 모델 이름
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

st.set_page_config(page_title="숨쉬는한의원 문진 · 치료계획", layout="wide")
st.title("🩺 숨쉬는한의원 문진 · 치료계획")
st.caption("※ 본 출력은 참고용이며, 진단·처방이 아닙니다. 최종 결정은 의료진의 판단에 따릅니다.")

# 사이드바 디버그
show_debug = st.sidebar.toggle("디버그 표시", value=False)

# -----------------------------
# API 호출 함수
# -----------------------------
def call_google_gl_api(prompt: str):
    if not API_KEY:
        return {"error": "API_KEY_NOT_SET", "message": "환경변수 GOOGLE_API_KEY 또는 GEMINI_API_KEY가 설정되지 않았습니다."}

    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(API_URL, json=payload, timeout=45)
        if resp.status_code != 200:
            return {"error": "HTTP_ERROR", "status": resp.status_code, "body": resp.text}
        data = resp.json()
        text = (
            data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text")
        )
        return {"text": text, "raw": data}
    except Exception as e:
        return {"error": "REQUEST_EXCEPTION", "message": str(e)}

def safe_json_from_text(text: str):
    if not text:
        return None
    import re
    m = re.search(r"\{[\s\S]*\}$", text.strip())
    try:
        return json.loads(m.group(0) if m else text)
    except Exception:
        return None

# -----------------------------
# 1) 환자 기본 정보
# -----------------------------
st.header("1. 환자 기본 정보")
c1, c2, c3 = st.columns(3)
with c1:
    p_name = st.text_input("이름")
with c2:
    p_age = st.number_input("나이", min_value=0, max_value=120, step=1)
with c3:
    p_bp = st.text_input("혈압·맥박 (예: 120/80, 72회)")

# -----------------------------
# 2) 문진 입력
# -----------------------------
st.header("2. 문진")

SYMPTOMS = ["머리","허리","어깨","발/목/뒤꿈치","무릎","손목","허벅지","뒷목 어깻죽지","등",
            "손","손가락","엉덩이/골반","팔꿈치","장단지","손/팔 저림","두통/어지러움",
            "설사","생리통","다리 감각 이상","변비","소화불량","불안 장애","불면","알레르지질환"]
symptoms = st.multiselect("현재 불편한 증상 (복수 선택)", SYMPTOMS)
symptom_etc = st.text_input("기타 증상 직접 입력")

onset = st.selectbox("증상 시작 시점", ["일주일 이내", "1주~1개월", "1개월~3개월", "3개월 이상"])
onset_date = st.text_input("발병일 (선택)")

CAUSES = ["사고(운동)","사고(교통사고)","사고(상해)","사고(일상생활)","음식","스트레스","원인모름","기존질환","생활습관 및 환경"]
causes = st.multiselect("증상 원인 (복수 선택)", CAUSES)
cause_detail = st.text_input("원인 세부(기존질환명/생활습관 등)")

history = st.text_area("과거 병력 / 복용중인 약물 / 현재 치료 (예: 아토피약 복용중)")
visit = st.selectbox("내원 빈도", ["매일 통원", "주 3~6회", "주 1~2회", "기타"])
visit_etc = st.text_input("기타 내원 빈도 (선택)")

# 환자 객체
patient = {
    "name": p_name,
    "age": p_age,
    "bp": p_bp,
    "symptoms": symptoms + ([symptom_etc] if symptom_etc else []),
    "onset": onset,
    "onset_date": onset_date,
    "causes": causes + ([cause_detail] if cause_detail else []),
    "history": history,
    "visit": visit if visit != "기타" else f"기타({visit_etc})"
}

if show_debug:
    st.sidebar.write("환경변수 로드됨?:", bool(API_KEY))
    st.sidebar.write("모델:", MODEL_NAME)

# -----------------------------
# 3) AI 요약
# -----------------------------
st.header("3. AI 요약 및 제안")

colA, colB = st.columns(2)

with colA:
    st.subheader("문진 요약")
    if st.button("① 요약 생성"):
        prompt_summary = f"""아래 환자 문진을 보기 좋게 요약하라. 진단/처방/추론 금지, 입력 재구성만.
---
이름: {patient['name'] or '-'}, 나이: {patient['age'] or '-'}, 혈압/맥박: {patient['bp'] or '-'}
주요 증상: {', '.join(patient['symptoms']) or '-'}
증상 시작: {patient['onset']}{' ('+patient['onset_date']+')' if patient['onset_date'] else ''}
원인: {', '.join(patient['causes']) or '-'}
과거 병력/약물/치료: {patient['history'] or '-'}
내원 빈도: {patient['visit'] or '-'}
"""
        out = call_google_gl_api(prompt_summary)
        if out.get("error"):
            st.error(out)
            if show_debug: st.exception(out)
        else:
            st.code(out.get("text") or "(응답 본문 없음)", language="markdown")
            if show_debug: st.write(out.get("raw"))

with colB:
    st.subheader("AI 제안 (참고)")
    if st.button("② 제안 생성"):
        prompt_plan = f"""
너는 내부 상담 보조 도구다. 아래 환자 문진을 바탕으로 JSON만 출력하라(텍스트 금지).

필수 필드:
- classification: "급성"|"만성"|"웰니스"
- duration: "1주"|"2주"|"3주"|"4주"|"1개월 이상"
- covered: ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"] 중 일부
- uncovered: ["약침","약침패치","테이핑요법","비급여 맞춤 한약"] 중 일부
- rationale: 근거
- objective_comment: 생활습관/재발예방 등 객관 코멘트
- caution: 병력/복용약 기반 주의사항 (정보 모호해도 반드시 작성)

[환자 문진(JSON)]
{json.dumps(patient, ensure_ascii=False, indent=2)}
"""
        out = call_google_gl_api(prompt_plan)
        if out.get("error"):
            st.error(out)
            if show_debug: st.exception(out)
        else:
            text = out.get("text", "")
            st.code(text or "(응답 본문 없음)", language="json")
            parsed = safe_json_from_text(text)
            if parsed:
                st.session_state["last_ai"] = parsed
            else:
                st.session_state["last_ai"] = None
                st.warning("JSON 파싱 실패: 원문을 확인하세요.")
            if show_debug: st.write(out.get("raw"))

# -----------------------------
# 4) 최종 치료계획 (의료진 확정 + AI 제안 병합)
# -----------------------------
st.header("4. 최종 치료계획")

c1, c2 = st.columns(2)
with c1:
    cls = st.selectbox("질환 분류(의료진 선택)", ["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"])
with c2:
    period = st.selectbox("치료 기간", ["1주","2주","3주","4주","1개월 이상"])

COVERED_ITEMS = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
UNCOVERED_ITEMS = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]

cov = st.multiselect("치료 항목(급여)", COVERED_ITEMS)
unc = st.multiselect("치료 항목(비급여)", UNCOVERED_ITEMS)
herb = st.radio("비급여 맞춤 한약 기간", ["선택 안 함","1개월","2개월","3개월"], horizontal=True)

if st.button("③ 최종 결과 생성 (AI 제안 포함)"):
    ai = st.session_state.get("last_ai")

    lines = []
    lines.append("=== AI 제안(참고) ===")
    if ai:
        lines.append(f"- 분류: {ai.get('classification','-')}")
        lines.append(f"- 기간: {ai.get('duration','-')}")
        lines.append(f"- 급여 후보: {', '.join(ai.get('covered') or []) or '-'}")
        lines.append(f"- 비급여 후보: {', '.join(ai.get('uncovered') or []) or '-'}")
        lines.append(f"근거: {ai.get('rationale','-')}")
        lines.append(f"📝 객관적 참고: {ai.get('objective_comment','-')}")
        caution = (ai.get("caution") or "").strip() or "특이사항 없음"
        lines.append(f"⚠️ 주의사항: {caution}")
    else:
        lines.append("(AI 제안 없음)")
    lines.append("")

    lines.append("=== 최종 치료계획 (의료진 확정) ===")
    lines.append(f"- 분류: {cls}")
    lines.append(f"- 기간: {period}")
    cov_line = ", ".join(cov) if cov else "-"
    unc_line = ", ".join(unc) if unc else "-"
    if herb != "선택 안 함":
        if "비급여 맞춤 한약" in unc_line:
            unc_line = unc_line.replace("비급여 맞춤 한약", f"비급여 맞춤 한약({herb})")
        else:
            unc_line = f"{unc_line}{'' if unc_line=='-' else ', ' }비급여 맞춤 한약({herb})"
    lines.append(f"- 급여: {cov_line}")
    lines.append(f"- 비급여: {unc_line}")
    lines.append("")
    lines.append("※ 본 계획은 의료진의 임상 판단과 환자 동의에 따라 확정되었으며, 상기 AI 출력은 참고자료로만 활용되었습니다.")

    st.subheader("✅ 출력")
    st.code("\n".join(lines), language="text")
