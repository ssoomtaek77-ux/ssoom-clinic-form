import streamlit as st
import google.generativeai as genai

# ========================
# 기본 설정
# ========================
st.set_page_config(page_title="일반 질환 기초 문진표 · 숨쉬는한의원", page_icon="☁️", layout="wide")

API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

TEXT_MODEL = "gemini-1.5-flash"

# ========================
# 유틸 함수
# ========================
def call_ai(prompt: str) -> str:
    try:
        model = genai.GenerativeModel(TEXT_MODEL)
        res = model.generate_content(prompt)
        return res.text
    except Exception as e:
        return f"❌ 오류: {e}"

# ========================
# UI
# ========================
st.title("일반 질환 기초 문진표")

# ------------------- 환자 문진 -------------------
with st.form("patient_form"):
    st.subheader("환자 기본정보")
    name = st.text_input("이름", value=st.session_state.get("name", ""))
    age = st.number_input("나이", 0, 120, st.session_state.get("age", 30))
    bp = st.text_input("혈압/맥박", value=st.session_state.get("bp", ""))

    st.subheader("현재 불편한 증상")
    symptoms = st.multiselect(
        "증상 선택",
        ["머리","허리","어깨","무릎","손목","두통/어지러움","불면","알레르기","기타"],
        default=st.session_state.get("symptoms", []),
    )
    symptom_etc = st.text_input("기타 증상", value=st.session_state.get("symptom_etc", ""))

    onset = st.selectbox("증상 시작 시점",
        ["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"],
        index=["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"].index(st.session_state.get("onset", "일주일 이내"))
    )
    causes = st.multiselect("증상 원인",
        ["사고","음식","스트레스","원인모름","기존질환","생활습관"],
        default=st.session_state.get("causes", [])
    )
    disease = st.text_input("기존질환 (선택)", value=st.session_state.get("disease", ""))
    lifestyle = st.text_input("생활습관/환경 (선택)", value=st.session_state.get("lifestyle", ""))

    history = st.text_area("과거 병력/복용 중인 약물/치료", value=st.session_state.get("history", ""))
    visit = st.selectbox("내원 빈도",
        ["매일 통원","주 3~6회","주 1~2회","기타"],
        index=["매일 통원","주 3~6회","주 1~2회","기타"].index(st.session_state.get("visit", "매일 통원"))
    )

    submitted = st.form_submit_button("① 문진 요약 생성")

# ------------------- 요약 및 AI 제안 -------------------
if submitted:
    # 입력값 세션에 저장
    st.session_state["name"] = name
    st.session_state["age"] = age
    st.session_state["bp"] = bp
    st.session_state["symptoms"] = symptoms
    st.session_state["symptom_etc"] = symptom_etc
    st.session_state["onset"] = onset
    st.session_state["causes"] = causes
    st.session_state["disease"] = disease
    st.session_state["lifestyle"] = lifestyle
    st.session_state["history"] = history
    st.session_state["visit"] = visit

    patient_data = f"""
이름: {name}, 나이: {age}
혈압/맥박: {bp}
증상: {", ".join(symptoms+[symptom_etc] if symptom_etc else symptoms)}
시작: {onset}
원인: {", ".join(causes)} {disease} {lifestyle}
과거/약물: {history}
내원: {visit}
"""

    st.subheader("문진 요약")
    summary = call_ai(f"다음 환자 문진 내용을 보기 좋게 요약:\n{patient_data}")
    st.session_state["summary"] = summary
    st.code(summary, language="markdown")

    st.subheader("AI 제안")
    plan_prompt = f"""
너는 한의원 상담 보조 도우미다.
환자 문진을 보고 JSON만 출력하라.

⚠️ 규칙:
1. covered와 uncovered에는 반드시 아래 리스트 중에서만 선택:
   covered = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
   uncovered = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]
2. covered/uncovered에 없는 건 절대 넣지 말 것.
3. 만약 다른 치료 아이디어가 있다면 반드시 extra_suggestions 배열에만 넣을 것.
4. caution 필드는 환자의 병력/복용약을 바탕으로 절대 빈칸 없이 작성.

[환자 문진]
{patient_data}
"""
    ai_plan = call_ai(plan_prompt)
    st.session_state["ai_plan"] = ai_plan
    st.code(ai_plan, language="markdown")

# ------------------- 치료계획 (항상 보이도록 고정) -------------------
st.subheader("최종 치료계획 (의료진 확정)")

cls = st.selectbox("질환 분류",
    ["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"],
    index=["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"].index(st.session_state.get("cls","급성질환(10~14일)"))
)
st.session_state["cls"] = cls

period = st.selectbox("치료 기간",
    ["1주","2주","3주","4주","1개월 이상"],
    index=["1주","2주","3주","4주","1개월 이상"].index(st.session_state.get("period","1주"))
)
st.session_state["period"] = period

cov = st.multiselect("치료 항목(급여)",
    ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"],
    default=st.session_state.get("cov", [])
)
st.session_state["cov"] = cov

unc = st.multiselect("치료 항목(비급여)",
    ["약침","약침패치","테이핑요법","비급여 맞춤 한약"],
    default=st.session_state.get("unc", [])
)
st.session_state["unc"] = unc

herb = st.radio("맞춤 한약 기간",
    ["선택 안 함","1개월","2개월","3개월"],
    index=["선택 안 함","1개월","2개월","3개월"].index(st.session_state.get("herb","선택 안 함"))
)
st.session_state["herb"] = herb

if st.button("최종 결과 생성"):
    summary = st.session_state.get("summary", "아직 생성되지 않음")
    ai_plan = st.session_state.get("ai_plan", "아직 제안 없음")

    final_text = f"""
=== 환자 문진 요약 ===
{summary}

=== Gemini 제안 ===
{ai_plan}

=== 최종 치료계획 (의료진 확정) ===
- 분류: {cls}
- 기간: {period}
- 급여: {", ".join(cov) if cov else "-"}
- 비급여: {", ".join(unc) if unc else "-"}
- 맞춤 한약: {herb if herb!="선택 안 함" else "-"}
"""
    st.text_area("최종 출력", final_text, height=300)
