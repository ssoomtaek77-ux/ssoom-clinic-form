import streamlit as st
import google.generativeai as genai
import json, re

# ========================
# 기본 설정
# ========================
st.set_page_config(page_title="일반 질환 기초 문진표", page_icon="☁️", layout="wide")

API_KEY = st.secrets.get("GOOGLE_API_KEY")
if not API_KEY:
    st.error("관리자: Streamlit Secrets에 GOOGLE_API_KEY를 설정하세요.")
    st.stop()
genai.configure(api_key=API_KEY)

MODEL = "gemini-1.5-flash"

# ========================
# 유틸 함수
# ========================
def call_ai(prompt: str) -> str:
    try:
        model = genai.GenerativeModel(MODEL)
        res = model.generate_content(prompt)
        return res.text
    except Exception as e:
        return f"❌ 오류: {e}"

# ========================
# 체크리스트 항목
# ========================
SYMPTOMS = ["머리","허리","어깨","무릎","손목","두통/어지러움","불면","알레르기","기타"]
CAUSES = ["사고","음식","스트레스","원인모름","기존질환","생활습관"]
COVERED_ITEMS = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
UNCOVERED_ITEMS = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]

# ========================
# 세션 상태 초기화
# ========================
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "ai_plan" not in st.session_state:
    st.session_state.ai_plan = ""

# ========================
# UI: 환자 입력
# ========================
st.title("일반 질환 기초 문진표")

st.subheader("환자 기본정보")
name = st.text_input("이름")
age = st.number_input("나이", 0, 120, 30)
bp = st.text_input("혈압/맥박")

st.subheader("1) 현재 불편한 증상")
symptoms = st.multiselect("증상 선택", SYMPTOMS)
symptom_etc = st.text_input("기타 증상 (선택)")

st.subheader("2) 증상 시작 시점")
onset = st.selectbox("선택", ["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"])

st.subheader("3) 증상 원인")
causes = st.multiselect("원인 선택", CAUSES)
disease = st.text_input("기존질환 (선택)")
lifestyle = st.text_input("생활습관/환경 (선택)")

st.subheader("4) 과거 병력/복용 중인 약물/치료")
history = st.text_area("내용 입력")

st.subheader("5) 내원 빈도")
visit = st.selectbox("선택", ["매일 통원","주 3~6회","주 1~2회","기타"])

# ========================
# 버튼: 문진 요약
# ========================
if st.button("① 문진 요약 생성"):
    patient_data = f"""
이름: {name}, 나이: {age}
혈압/맥박: {bp}
증상: {", ".join(symptoms+[symptom_etc] if symptom_etc else symptoms)}
증상 시작: {onset}
원인: {", ".join(causes)} {disease} {lifestyle}
과거/약물: {history}
내원 빈도: {visit}
"""
    st.session_state.summary = call_ai(f"다음 환자 문진 내용을 보기 좋게 요약:\n{patient_data}")

st.subheader("문진 요약")
st.write(st.session_state.summary or "(아직 요약 없음)")

# ========================
# 버튼: AI 제안
# ========================
if st.button("② AI 제안 생성"):
    patient_data = f"""
이름: {name}, 나이: {age}
혈압/맥박: {bp}
증상: {", ".join(symptoms+[symptom_etc] if symptom_etc else symptoms)}
증상 시작: {onset}
원인: {", ".join(causes)} {disease} {lifestyle}
과거/약물: {history}
내원 빈도: {visit}
"""
    plan_prompt = f"""
너는 한의원 상담 보조 도우미다.
내 카테고리 안에서 추천하되, 추가로 필요하다고 생각되는 건 extra_suggestion으로 제안해라.

필수 필드:
- classification: 급성/만성/웰니스
- duration: 1주~1개월 이상 중 택1
- covered: {COVERED_ITEMS} 중 선택
- uncovered: {UNCOVERED_ITEMS} 중 선택
- rationale: 권장 이유
- objective_comment: 생활습관/예방
- caution: 복용약/병력 기반 주의사항 (없으면 "특이사항 없음")
- extra_suggestion: 카테고리 외 추가 제안

문진 내용:
{patient_data}
"""
    raw = call_ai(plan_prompt)
    try:
        m = re.search(r"\{[\s\S]*\}", raw)
        parsed = json.loads(m.group(0)) if m else {}
        st.session_state.ai_plan = parsed
    except:
        st.session_state.ai_plan = {"raw": raw}

st.subheader("AI 제안")
st.write(st.session_state.ai_plan or "(아직 제안 없음)")

# ========================
# 최종 치료계획 (항상 고정)
# ========================
st.subheader("③ 최종 치료계획 (의료진 확정)")
cls = st.selectbox("질환 분류", ["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"])
period = st.selectbox("치료 기간", ["1주","2주","3주","4주","1개월 이상"])
cov = st.multiselect("치료 항목(급여)", COVERED_ITEMS)
unc = st.multiselect("치료 항목(비급여)", UNCOVERED_ITEMS)
herb = st.radio("맞춤 한약 기간", ["선택 안 함","1개월","2개월","3개월"], index=0)

if st.button("최종 결과 생성"):
    final_text = f"""
=== 환자 문진 요약 ===
{st.session_state.summary}

=== Gemini 제안 ===
{st.session_state.ai_plan}

=== 최종 치료계획 (의료진 확정) ===
- 분류: {cls}
- 기간: {period}
- 급여: {", ".join(cov) if cov else "-"}
- 비급여: {", ".join(unc) if unc else "-"}
- 맞춤 한약: {herb if herb!="선택 안 함" else "-"}
"""
    st.text_area("최종 출력", final_text, height=300)
