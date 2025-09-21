import streamlit as st
import requests
import os

# -----------------------------
# 환경 변수에서 API 키 불러오기
# (Streamlit Cloud → Settings → Secrets → GEMINI_API_KEY 설정)
# -----------------------------
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = "gemini-pro"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

st.set_page_config(page_title="숨쉬는한의원 문진 · 치료계획", layout="wide")

st.title("🩺 숨쉬는한의원 문진 · 치료계획 웹앱")
st.write("작성된 문진 내용은 진료 목적 외에는 사용되지 않으며, 개인정보 보호법에 따라 안전하게 관리됩니다.")

# -----------------------------
# 환자 기본 정보 입력
# -----------------------------
st.header("1. 환자 기본 정보")
col1, col2, col3 = st.columns(3)
with col1:
    p_name = st.text_input("이름")
with col2:
    p_age = st.number_input("나이", min_value=0, max_value=120, step=1)
with col3:
    p_bp = st.text_input("혈압·맥박 (예: 120/80, 72회)")

# -----------------------------
# 문진 입력
# -----------------------------
st.header("2. 문진")

symptoms = st.multiselect(
    "현재 불편한 증상",
    ["머리","허리","어깨","발/목/뒤꿈치","무릎","손목","허벅지","뒷목 어깻죽지","등",
     "손","손가락","엉덩이/골반","팔꿈치","장단지","손/팔 저림","두통/어지러움",
     "설사","생리통","다리 감각 이상","변비","소화불량","불안 장애","불면","알레르기질환"]
)
symptom_etc = st.text_input("기타 증상")

onset = st.selectbox("증상 시작 시점", ["일주일 이내", "1주~1개월", "1개월~3개월", "3개월 이상"])
onset_date = st.text_input("발병일 (선택)")

causes = st.multiselect("증상 원인", ["사고(운동)","사고(교통사고)","사고(상해)","사고(일상생활)",
                                    "음식","스트레스","원인모름","기존질환","생활습관 및 환경"])
cause_detail = st.text_input("원인 세부내용 (기존질환명, 생활습관 등)")

history = st.text_area("과거 병력 / 복용중인 약물 / 현재 치료")

visit = st.selectbox("내원 빈도", ["매일 통원", "주 3~6회", "주 1~2회", "기타"])
visit_etc = st.text_input("기타 내원 빈도")

# -----------------------------
# 요약 & Gemini 제안 버튼
# -----------------------------
st.header("3. AI 요약 및 제안")

def call_gemini(prompt):
    if not API_KEY:
        return "❌ API 키가 설정되지 않았습니다."
    try:
        res = requests.post(API_URL, json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}]
        })
        data = res.json()
        return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "⚠️ 응답 없음")
    except Exception as e:
        return f"에러 발생: {e}"

if st.button("① 문진 요약 생성"):
    patient_text = f"""
    이름: {p_name}, 나이: {p_age}, 혈압/맥박: {p_bp}
    증상: {', '.join(symptoms + ([symptom_etc] if symptom_etc else []))}
    시작 시점: {onset} {onset_date}
    원인: {', '.join(causes)} {cause_detail}
    과거 병력/약물/치료: {history}
    내원 빈도: {visit} {visit_etc}
    """

    prompt = f"""
    아래 환자 문진 내용을 보기 좋게 요약해줘.
    단순 재구성만 하고, SOAP 차팅은 하지 마.
    ---
    {patient_text}
    """
    summary = call_gemini(prompt)
    st.subheader("📌 환자 문진 요약")
    st.code(summary, language="markdown")

if st.button("② Gemini 제안 생성"):
    patient_json = {
        "name": p_name,
        "age": p_age,
        "bp": p_bp,
        "symptoms": symptoms + ([symptom_etc] if symptom_etc else []),
        "onset": onset,
        "onset_date": onset_date,
        "causes": causes,
        "cause_detail": cause_detail,
        "history": history,
        "visit": visit if visit != "기타" else f"기타({visit_etc})"
    }

    prompt = f"""
    너는 숨쉬는한의원 내부 상담 보조 도구다.
    아래 환자 문진을 기반으로 객관적인 제안과 주관적인 참고 의견을 함께 제공해라.
    1) 분류 (급성/만성/웰니스)
    2) 권장 치료기간 (주 단위 또는 1개월 이상)
    3) 권장 치료 항목 (급여/비급여 각각)
    4) 약물 병용 시 주의사항 (예: 아토피 약 복용 시 참고사항)
    5) 간단한 근거 요약

    환자 문진:
    {patient_json}
    """
    plan = call_gemini(prompt)
    st.subheader("🤖 Gemini 제안")
    st.code(plan, language="markdown")

# -----------------------------
# 치료 계획 체크
# -----------------------------
st.header("4. 치료계획 (의료진 확정)")

col1, col2 = st.columns(2)
with col1:
    cls = st.selectbox("질환 분류", ["급성질환(10~14일)", "만성질환(15일~3개월)", "웰니스(3개월 이상)"])
with col2:
    period = st.selectbox("치료 기간", ["1주", "2주", "3주", "4주", "1개월 이상"])

covered = st.multiselect("치료 항목 (급여)", ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"])
uncovered = st.multiselect("치료 항목 (비급여)", ["약침","약침패치","테이핑요법","비급여 맞춤 한약"])
herb = st.radio("비급여 맞춤 한약 기간", ["선택 안 함","1개월","2개월","3개월"])

if st.button("③ 최종 치료계획 생성"):
    final_text = f"""
    === 환자 문진 요약 ===
    (위 요약 참고)

    === Gemini 제안 ===
    (위 AI 제안 참고)

    === 최종 치료계획 (의료진 확정) ===
    - 분류: {cls}
    - 기간: {period}
    - 급여 항목: {', '.join(covered) if covered else '-'}
    - 비급여 항목: {', '.join(uncovered) if uncovered else '-'} {'' if herb == '선택 안 함' else f'(+ {herb} 한약)'}
    """
    st.subheader("✅ 최종 치료계획")
    st.code(final_text, language="markdown")

