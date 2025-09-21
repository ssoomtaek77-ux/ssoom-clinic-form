import streamlit as st
import google.generativeai as genai
import json

# ========================
# 기본 설정
# ========================
st.set_page_config(page_title="일반 질환 기초 문진표", page_icon="☁️", layout="wide")

API_KEY = st.secrets.get("GOOGLE_API_KEY")
if not API_KEY:
    st.error("⚠️ 관리자: Streamlit Secrets에 GOOGLE_API_KEY를 설정하세요.")
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

def call_ai_json(prompt: str):
    try:
        model = genai.GenerativeModel(MODEL)
        res = model.generate_content(prompt)
        raw = res.text
        # JSON만 추출
        m = raw.strip().split("```")
        candidate = None
        for block in m:
            if block.strip().startswith("{"):
                candidate = block
                break
        if candidate:
            return json.loads(candidate)
        else:
            return None
    except Exception as e:
        return {"error": str(e)}

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
        ["머리","허리","어깨","발/목/뒤꿈치","무릎","손목","허벅지","뒷목 어깻죽지",
         "등","손","손가락","엉덩이/골반","팔꿈치","장단지","손/팔 저림",
         "두통/어지러움","설사","생리통","다리 감각 이상","변비","소화불량",
         "불안 장애","불면","알레르지질환"]
    )
    symptom_etc = st.text_input("기타 증상 (선택)")

    st.subheader("2) 증상 시작 시점")
    onset = st.selectbox("선택", ["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"])
    onset_date = st.text_input("발병일 (선택)")

    st.subheader("3) 증상 원인")
    causes = st.multiselect("원인 선택", [
        "사고(운동)","사고(교통사고)","사고(상해)","사고(일상생활)",
        "음식","스트레스","원인모름","기존질환","생활습관 및 환경"
    ])
    disease = st.text_input("기존질환 (선택)")
    lifestyle = st.text_input("생활습관/환경 (선택)")

    st.subheader("4) 과거 병력/복용 중인 약물/치료")
    history = st.text_area("내용 입력")

    st.subheader("5) 내원 빈도")
    visit = st.selectbox("선택", ["매일 통원","주 3~6회","주 1~2회","기타"])

    submitted = st.form_submit_button("① 문진 요약 생성")

# ========================
# 제출 후 처리
# ========================
if submitted:
    patient_data = f"""
이름: {name}, 나이: {age}
혈압/맥박: {bp}
증상: {", ".join(symptoms+[symptom_etc] if symptom_etc else symptoms)}
증상 시작: {onset}{(" ("+onset_date+")") if onset_date else ""}
원인: {", ".join(causes)} {disease} {lifestyle}
과거/약물: {history}
내원 빈도: {visit}
"""

    # ----------------
    # ① 문진 요약
    # ----------------
    st.subheader("문진 요약")
    summary_prompt = f"다음 환자 문진 내용을 보기 좋게 요약:\n{patient_data}"
    summary = call_ai(summary_prompt)
    st.write(summary)

    # ----------------
    # ② AI 제안 (JSON 출력 강제)
    # ----------------
    st.subheader("AI 제안 (분류/치료/기간/주의사항)")
    plan_prompt = f"""
너는 한의원 상담 보조 도우미다.
아래 환자 문진을 보고 JSON만 출력하라.

필수 필드:
- classification: "급성"|"만성"|"웰니스"
- duration: "1주"|"2주"|"3주"|"4주"|"1개월 이상"
- covered: ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
- uncovered: ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]
- rationale: 권장 근거
- objective_comment: 생활습관/재발예방 등 객관 코멘트
- caution: 환자의 병력/복용약 기반 주의사항 (빈칸 금지)

환자 문진:
{patient_data}
"""
    ai_json = call_ai_json(plan_prompt)

    if ai_json:
        caution_text = ai_json.get("caution","")
        # fallback 로직
        if not caution_text:
            caution_text = "특이사항 없음 (AI 출력 누락)"
        if "아토피" in history:
            caution_text += "\n(자동 안내) 아토피 관련 약물 복용 가능성 → 항히스타민제/스테로이드 계열 병행 시 졸림·피로/피부자극 등 확인 필요."

        ai_json["caution"] = caution_text

        st.json(ai_json)
    else:
        st.warning("AI 제안 생성 실패")

    # ----------------
    # ③ 최종 치료계획 (의료진 확정)
    # ----------------
    st.subheader("최종 치료계획 (의료진 확정)")

    cls = st.selectbox("질환 분류", ["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"])
    period = st.selectbox("치료 기간", ["1주","2주","3주","4주","1개월 이상"])
    cov = st.multiselect("치료 항목(급여)", ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"])
    unc = st.multiselect("치료 항목(비급여)", ["약침","약침패치","테이핑요법","비급여 맞춤 한약"])
    herb = st.radio("맞춤 한약 기간", ["선택 안 함","1개월","2개월","3개월"], index=0)

    if st.button("최종 결과 생성"):
        final_text = f"""
=== 환자 문진 요약 ===
{summary}

=== AI 제안 ===
{json.dumps(ai_json, ensure_ascii=False, indent=2) if ai_json else "(없음)"}

=== 최종 치료계획 (의료진 확정) ===
- 분류: {cls}
- 기간: {period}
- 급여: {", ".join(cov) if cov else "-"}
- 비급여: {", ".join(unc) if unc else "-"}
- 맞춤 한약: {herb if herb!="선택 안 함" else "-"}
"""
        st.text_area("최종 출력", final_text, height=400)
