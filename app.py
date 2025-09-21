import streamlit as st
import google.generativeai as genai
import json

# 🔑 API Key 불러오기 (Streamlit Secrets)
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# -------------------------------
# 세션 상태 초기화
# -------------------------------
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "ai_plan" not in st.session_state:
    st.session_state.ai_plan = ""
if "final_plan" not in st.session_state:
    st.session_state.final_plan = ""

# -------------------------------
# 제목
# -------------------------------
st.title("🩺 일반 질환 기초 문진표 · 숨쉬는한의원")

# -------------------------------
# 입력창
# -------------------------------
st.subheader("📋 문진 입력")
patient_data = st.text_area("환자 문진 내용을 입력하세요", height=150)

# -------------------------------
# 문진 요약 생성
# -------------------------------
if st.button("① 요약 생성"):
    if not patient_data.strip():
        st.warning("환자 문진 내용을 입력해주세요.")
    else:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            아래 환자 문진 내용을 간단히 요약해줘.

            [문진 내용]
            {patient_data}
            """
            response = model.generate_content(prompt)
            st.session_state.summary = response.text
        except Exception as e:
            st.error(f"요약 생성 중 오류 발생: {e}")

# -------------------------------
# 문진 요약 출력 + 복사 버튼
# -------------------------------
with st.container():
    st.markdown("### 📌 문진 요약")
    if st.session_state.summary:
        st.text_area("요약 결과", value=st.session_state.summary, height=150, key="summary_box")
        st.button("📋 요약 복사", on_click=lambda: st.session_state.update(copy_sum=st.session_state.summary))
    else:
        st.info("아직 생성하지 않았습니다.")

# -------------------------------
# AI 제안 생성
# -------------------------------
if st.button("② AI 제안 생성"):
    if not st.session_state.summary:
        st.warning("먼저 문진 요약을 생성하세요.")
    else:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            plan_prompt = f"""
            너는 한의원 상담 보조 도우미다.
            환자 요약을 기반으로 JSON 형태의 치료 계획 제안을 만들어라.

            ⚠️ 규칙:
            1. covered(급여 항목)과 uncovered(비급여 항목)는 반드시 아래 리스트 중에서만 선택:
               covered = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
               uncovered = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]
            2. covered/uncovered에 없는 치료법은 절대 넣지 마라.
            3. 만약 다른 추가 치료 아이디어가 있다면 반드시 extra_suggestions 배열에만 넣어라.
            4. rationale(근거), objective_comment(객관적 코멘트), caution(주의사항)은 반드시 채워라.

            JSON 예시:
            {{
              "classification": "만성",
              "duration": "4주",
              "covered": ["전침","체질침"],
              "uncovered": ["약침"],
              "extra_suggestions": ["운동치료 병행", "식이조절 지도"],
              "rationale": "증상 기간 및 병력 고려",
              "objective_comment": "수면·스트레스 관리 권장",
              "caution": "혈압약 복용 중으로 어지럼증 주의"
            }}

            [환자 요약]
            {st.session_state.summary}
            """

            response = model.generate_content(plan_prompt)
            st.session_state.ai_plan = response.text

        except Exception as e:
            st.error(f"AI 제안 생성 중 오류 발생: {e}")

# -------------------------------
# AI 제안 출력 + 복사 버튼
# -------------------------------
with st.container():
    st.markdown("### 🤖 AI 제안 (분류/치료/기간/주의사항)")
    if st.session_state.ai_plan:
        st.text_area("AI 제안 결과", value=st.session_state.ai_plan, height=250, key="ai_plan_box")
        st.button("📋 제안 복사", on_click=lambda: st.session_state.update(copy_ai=st.session_state.ai_plan))
    else:
        st.info("아직 제안 없음")

# -------------------------------
# 최종 치료계획 (수정 가능)
# -------------------------------
st.markdown("### 🩺 최종 치료계획 (의료진 확정)")
st.session_state.final_plan = st.text_area(
    "최종 치료계획을 입력하세요",
    value=st.session_state.final_plan,
    height=200,
    key="final_plan_box"
)

st.button("📋 최종 계획 복사", on_click=lambda: st.session_state.update(copy_final=st.session_state.final_plan))
