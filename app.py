import streamlit as st
import google.generativeai as genai

# ========================
# 기본 설정
# ========================
st.set_page_config(page_title="일반 질환 기초 문진표", page_icon="☁️", layout="wide")

# 👉 Streamlit Secrets에서 API 키 읽기
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

MODEL = "gemini-1.5-flash"   # ⚡️쿼터 효율 좋은 모델 (pro 대신 flash)

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

def copy_button(label, text, key):
    """복사 버튼: 텍스트를 클립보드에 복사"""
    st.code(text or "출력 없음")
    st.button(label, key=key, on_click=lambda: st.session_state.update({"_copy": text}))

# ========================
# UI 구성
# ========================
st.title("☁️ 일반 질환 기초 문진표")
st.caption("작성하신 문진 내용은 진료 목적 외에는 사용되지 않으며, 개인정보 보호법에 따라 안전하게 관리됩니다.")

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

# ========================
# 문진 데이터 정리
# ========================
patient_data = f"""
이름: {name}, 나이: {age}
혈압/맥박: {bp}
증상: {", ".join(symptoms+[symptom_etc] if symptom_etc else symptoms)}
증상 시작: {onset}
원인: {", ".join(causes)} {disease} {lifestyle}
과거/약물: {history}
내원 빈도: {visit}
"""

# ========================
# 문진 요약
# ========================
st.subheader("📌 문진 요약")
if submitted:
    summary = call_ai(f"다음 환자 문진 내용을 보기 좋게 요약:\n{patient_data}")
    st.write(summary)
    copy_button("요약 복사", summary, key="copy_sum")
else:
    st.info("아직 생성하지 않았습니다.")

# ========================
# AI 제안
# ========================
st.subheader("🤖 AI 제안 (분류/치료/기간/주의사항)")
if submitted:
    plan_prompt = f"""
너는 한의원 상담 보조 도우미다.
환자 문진을 보고:
1) 급성/만성/웰니스 분류
2) 권장 치료기간
3) 권장 급여/비급여 항목 (항상 내가 제공한 카테고리 안에서만 선택)
4) 복용 중 약물이 있다면 병용 시 주의사항

문진 내용:
{patient_data}
"""
    ai_plan = call_ai(plan_prompt)
    st.write(ai_plan)
    copy_button("AI 제안 복사", ai_plan, key="copy_plan")
else:
    st.info("아직 생성하지 않았습니다.")

# ========================
# 최종 치료계획
# ========================
st.subheader("🩺 최종 치료계획 (의료진 확정)")

cls = st.selectbox("질환 분류", ["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"])
period = st.selectbox("치료 기간", ["1주","2주","3주","4주","1개월 이상"])

cov = st.multiselect("치료 항목(급여)", ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"])
unc = st.multiselect("치료 항목(비급여)", ["약침","약침패치","테이핑요법","비급여 맞춤 한약"])
herb = st.radio("맞춤 한약 기간", ["선택 안 함","1개월","2개월","3개월"], index=0)

if st.button("③ 최종 결과 생성"):
    final_text = f"""
=== 환자 문진 요약 ===
{summary if submitted else "(요약 없음)"}

=== Gemini 제안 ===
{ai_plan if submitted else "(AI 제안 없음)"}

=== 최종 치료계획 (의료진 확정) ===
- 분류: {cls}
- 기간: {period}
- 급여: {", ".join(cov) if cov else "-"}
- 비급여: {", ".join(unc) if unc else "-"}
- 맞춤 한약: {herb if herb!="선택 안 함" else "-"}
"""
    st.text_area("최종 출력", final_text, height=300)
    copy_button("최종 결과 복사", final_text, key="copy_final")
