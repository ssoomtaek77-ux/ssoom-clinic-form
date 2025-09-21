import streamlit as st
import requests
import json

# ==============================
# 0) API 키 세팅 (Streamlit Secrets 사용)
# ==============================
API_KEY = st.secrets["GOOGLE_API_KEY"]   # Streamlit > Settings > Secrets 에 GOOGLE_API_KEY 넣기
MODEL = "gemini-1.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# ==============================
# 1) 체크리스트 카테고리
# ==============================
SYMPTOMS = ["머리","허리","어깨","발/목/뒤꿈치","무릎","손목","허벅지","뒷목 어깻죽지",
            "등","손","손가락","엉덩이/골반","팔꿈치","장단지","손/팔 저림","두통/어지러움",
            "설사","생리통","다리 감각 이상","변비","소화불량","불안 장애","불면","알레르기질환"]

CAUSES = ["사고(운동)","사고(교통사고)","사고(상해)","사고(일상생활)","음식","스트레스",
          "원인모름","기존질환","생활습관 및 환경"]

COVERED_ITEMS = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
UNCOVERED_ITEMS = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]

# ==============================
# 2) 유틸 함수
# ==============================
def call_gemini(prompt: str) -> str:
    res = requests.post(API_URL, headers={"Content-Type": "application/json"},
                        data=json.dumps({"contents":[{"role":"user","parts":[{"text":prompt}]}]}))
    try:
        return res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "(AI 응답 없음)"

def copy_to_clipboard(label, text, key):
    """Streamlit Cloud에서도 동작하는 JS 복사 버튼"""
    copy_script = f"""
    <textarea id="copy-text-{key}" style="position: absolute; left: -9999px;">{text}</textarea>
    <button onclick="navigator.clipboard.writeText(document.getElementById('copy-text-{key}').value)">📋 {label}</button>
    """
    st.markdown(copy_script, unsafe_allow_html=True)

# ==============================
# 3) UI 시작
# ==============================
st.title("🩺 일반 질환 기초 문진표 · 숨쉬는한의원")
st.caption("※ 작성하신 문진 내용은 진료 목적 외에는 사용되지 않으며, 개인정보 보호법에 따라 안전하게 관리됩니다.")

# --- 기본 정보
st.header("기본정보")
col1, col2 = st.columns(2)
with col1:
    p_name = st.text_input("이름", "")
with col2:
    p_age = st.number_input("나이", min_value=0, max_value=120, step=1)
p_bp = st.text_input("혈압·맥박", placeholder="예) 120/80, 맥박 72회")

# --- 문진
st.header("문진")
sym = st.multiselect("현재 불편한 증상", SYMPTOMS)
sym_etc = st.text_input("기타 증상 직접 입력")
if sym_etc:
    sym.append(sym_etc)

col1, col2 = st.columns(2)
with col1:
    onset = st.selectbox("증상 시작 시점", ["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"])
with col2:
    onset_date = st.text_input("발병일 (선택)", "")

cause = st.multiselect("증상 원인", CAUSES)
cause_etc = st.text_input("기타 원인 직접 입력")
if cause_etc:
    cause.append(cause_etc)

history = st.text_area("과거 병력/약물", "")
visit = st.selectbox("내원 빈도", ["매일 통원","주 3~6회","주 1~2회","기타"])

# ==============================
# 4) 문진 요약
# ==============================
st.subheader("① 문진 요약")
if st.button("요약 생성"):
    prompt = f"""환자 문진 요약:
- 이름/나이: {p_name or "-"} / {p_age or "-"}
- 혈압/맥박: {p_bp or "-"}
- 주요 증상: {", ".join(sym) if sym else "-"}
- 증상 시작: {onset}{f" ({onset_date})" if onset_date else ""}
- 원인: {", ".join(cause) if cause else "-"}
- 과거 병력/약물: {history or "-"}
- 내원 빈도: {visit}"""
    st.session_state["summary"] = call_gemini(prompt)

summary_text = st.session_state.get("summary","아직 생성하지 않았습니다.")
st.text_area("요약 결과", summary_text, height=150)
copy_to_clipboard("요약 복사", summary_text, "sum")

# ==============================
# 5) AI 제안
# ==============================
st.subheader("② AI 제안")
if st.button("제안 생성"):
    ask = f"""
너는 숨쉬는한의원 내부 상담 보조 도구다.
아래 환자 문진을 바탕으로 JSON을 출력하라.

필수 필드:
- classification: "급성"|"만성"|"웰니스"
- duration: "1주"|"2주"|"3주"|"4주"|"1개월 이상"
- covered: {COVERED_ITEMS} 중 추천
- uncovered: {UNCOVERED_ITEMS} 중 추천
- extra: 카테고리에 없는 추가 치료법 제안 (있으면)
- rationale: 근거
- objective_comment: 생활습관/재발예방 조언
- caution: 약물/병력 주의사항
"""
    patient = {
        "name": p_name, "age": p_age, "bp": p_bp,
        "symptoms": sym, "onset": onset, "onset_date": onset_date,
        "causes": cause, "history": history, "visit": visit
    }
    prompt = ask + "\n[환자 문진]\n" + json.dumps(patient,ensure_ascii=False,indent=2)
    raw = call_gemini(prompt)

    try:
        parsed = json.loads(raw.split("{",1)[1].rsplit("}",1)[0].join(["{","}"]))
    except:
        parsed = None

    if parsed:
        st.session_state["ai"] = parsed
    else:
        st.session_state["ai"] = {"error": raw}

ai_plan = st.session_state.get("ai", {})
st.text_area("AI 제안 결과", json.dumps(ai_plan, ensure_ascii=False, indent=2), height=220)
copy_to_clipboard("제안 복사", json.dumps(ai_plan, ensure_ascii=False, indent=2), "ai")

# ==============================
# 6) 최종 치료계획
# ==============================
st.subheader("③ 최종 치료계획 (의료진 확정)")

col1, col2 = st.columns(2)
with col1:
    cls = st.selectbox("질환 분류", ["급성질환","만성질환","웰니스"])
with col2:
    period = st.selectbox("치료 기간", ["1주","2주","3주","4주","1개월 이상"])

cov = st.multiselect("치료 항목 (급여)", COVERED_ITEMS)
unc = st.multiselect("치료 항목 (비급여)", UNCOVERED_ITEMS)
herb = st.selectbox("맞춤 한약", ["선택 안 함","비염 한약","체질 한약","보약","기타"])

if st.button("최종 결과 생성"):
    ai_data = st.session_state.get("ai", {})
    final_text = f"""
=== 환자 문진 요약 ===
{summary_text}

=== AI 제안 ===
{json.dumps(ai_data, ensure_ascii=False, indent=2)}

=== 최종 치료계획 (의료진 확정) ===
- 분류: {cls} {(ai_data.get("classification") if isinstance(ai_data, dict) else "")}
- 기간: {period} {(ai_data.get("duration") if isinstance(ai_data, dict) else "")}
- 급여: {", ".join(cov) if cov else "-"}
- 비급여: {", ".join(unc) if unc else "-"}
- 맞춤 한약: {herb if herb!="선택 안 함" else "-"}

※ 고지: 본 계획은 의료진의 임상 판단과 환자 동의에 따라 확정되었으며, AI 출력은 참고자료로만 활용됩니다.
"""
    st.session_state["final"] = final_text

final_text = st.session_state.get("final","아직 생성하지 않았습니다.")
st.text_area("최종 출력", final_text, height=300)
copy_to_clipboard("최종 결과 복사", final_text, "final")
