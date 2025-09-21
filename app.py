import streamlit as st
import google.generativeai as genai

# ========================
# 기본 설정
# ========================
st.set_page_config(page_title="일반 질환 기초 문진표", page_icon="☁️", layout="wide")

API_KEY = st.secrets.get("GOOGLE_API_KEY")
if not API_KEY:
    st.error("관리자: Streamlit Secrets에 GOOGLE_API_KEY를 설정하세요.")
    st.stop()
genai.configure(api_key=API_KEY)

MODEL = "gemini-1.5-pro"

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
# UI 구성
# ========================
st.title("일반 질환 기초 문진표")

with st.form("patient_form"):
    st.subheader("환자 기본정보")
    name = st.text_input("이름")
    age = st.number_input("나이", 0, 120, 30)
    bp = st.text_input("혈압/맥박")

    st.subheader("1) 현재 불편한 증상")
    symptoms = st.multiselect(
        "증상 선택",
        ["머리","허리","어깨","무릎","손목","두통/어지러움","불면","알레르기","기타"],
    )
    symptom_etc = st.text_input("기타 증상 (선택)")

    st.subheader("2) 증상 시작 시점")
    onset = st.selectbox("선택", ["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"])

    st.subheader("3) 증상 원인")
    causes = st.multiselect("원인 선택", ["사고","음식","스트레스","원인모름","기존질환","생활습관"])
    disease = st.text_input("기존질환 (선택)")
    lifestyle = st.text_input("생활습관/환경 (선택)")

    st.subheader("4) 과거 병력/복용 중인 약물/치료")
    history = st.text_area("내용 입력")

    st.subheader("5) 내원 빈도")
    visit = st.selectbox("선택", ["매일 통원","주 3~6회","주 1~2회","기타"])

    submitted = st.form_submit_button("① 문진 요약 생성")

if submitted:
    patient_data = f"""
이름: {name}, 나이: {age}
혈압/맥박: {bp}
증상: {", ".join(symptoms+[symptom_etc] if symptom_etc else symptoms)}
증상 시작: {onset}
원인: {", ".join(causes)} {disease} {lifestyle}
과거/약물: {history}
내원 빈도: {visit}
"""
    st.subheader("문진 요약")
    summary = call_ai(f"다음 환자 문진 내용을 보기 좋게 요약:\n{patient_data}")
    st.write(summary)

    st.subheader("② AI 제안 (분류/치료/기간/주의사항)")
    plan_prompt = f"""
너는 한의원 상담 보조 도우미다.
환자 문진을 보고:
1) 급성/만성/웰니스 분류
2) 권장 치료기간
3) 권장 급여/비급여 항목
4) 복용 중 약물이 있다면 병용 시 주의사항

문진 내용:
{patient_data}
"""
    ai_plan = call_ai(plan_prompt)
    st.write(ai_plan)

    st.subheader("③ 최종 치료계획 (의료진 확정)")
    cls = st.selectbox("질환 분류", ["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"])
    period = st.selectbox("치료 기간", ["1주","2주","3주","4주","1개월 이상"])

    cov = st.multiselect("치료 항목(급여)", ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"])
    unc = st.multiselect("치료 항목(비급여)", ["약침","약침패치","테이핑요법","비급여 맞춤 한약"])
    herb = st.radio("맞춤 한약 기간", ["선택 안 함","1개월","2개월","3개월"], index=0)

    if st.button("최종 결과 생성"):
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
