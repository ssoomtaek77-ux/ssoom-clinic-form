import streamlit as st
import google.generativeai as genai

# ========================
# 기본 설정
# ========================
st.set_page_config(page_title="일반 질환 기초 문진표 · 숨쉬는한의원", page_icon="☁️", layout="wide")

# 🔑 API 키 (Streamlit Secrets)
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

TEXT_MODEL = "gemini-1.5-flash"

# ========================
# 초기 세션값 (한 번만 세팅)
# ========================
defaults = {
    "name":"", "age":30, "bp":"",
    "symptoms":[], "symptom_etc":"",
    "onset":"일주일 이내", "causes":[], "disease":"", "lifestyle":"",
    "history":"", "visit":"매일 통원",
    "patient_data":"", "summary":"", "ai_plan":"",
    "cls":"급성질환(10~14일)", "period":"1주",
    "cov":[], "unc":[], "herb":"선택 안 함",
    "final_text":""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

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

def build_patient_data():
    syms = st.session_state["symptoms"][:]
    if st.session_state["symptom_etc"]:
        syms.append(st.session_state["symptom_etc"])
    return f"""
이름: {st.session_state['name']}, 나이: {st.session_state['age']}
혈압/맥박: {st.session_state['bp']}
증상: {", ".join(syms)}
시작: {st.session_state['onset']}
원인: {", ".join(st.session_state['causes'])} {st.session_state['disease']} {st.session_state['lifestyle']}
과거/약물: {st.session_state['history']}
내원: {st.session_state['visit']}
""".strip()

# ========================
# UI
# ========================
st.title("일반 질환 기초 문진표")

# ------------------- 환자 문진 (폼 제거, 위젯-세션 직접 연결) -------------------
st.subheader("환자 기본정보")
st.session_state["name"] = st.text_input("이름", value=st.session_state["name"])
st.session_state["age"] = st.number_input("나이", 0, 120, value=int(st.session_state["age"]))
st.session_state["bp"] = st.text_input("혈압/맥박", value=st.session_state["bp"])

st.subheader("현재 불편한 증상")
st.session_state["symptoms"] = st.multiselect(
    "증상 선택",
    ["머리","허리","어깨","무릎","손목","두통/어지러움","불면","알레르기","기타"],
    default=st.session_state["symptoms"],
)
st.session_state["symptom_etc"] = st.text_input("기타 증상", value=st.session_state["symptom_etc"])

st.session_state["onset"] = st.selectbox(
    "증상 시작 시점",
    ["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"],
    index=["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"].index(st.session_state["onset"])
)
st.session_state["causes"] = st.multiselect(
    "증상 원인",
    ["사고","음식","스트레스","원인모름","기존질환","생활습관"],
    default=st.session_state["causes"]
)
st.session_state["disease"] = st.text_input("기존질환 (선택)", value=st.session_state["disease"])
st.session_state["lifestyle"] = st.text_input("생활습관/환경 (선택)", value=st.session_state["lifestyle"])

st.session_state["history"] = st.text_area("과거 병력/복용 중인 약물/치료", value=st.session_state["history"])
st.session_state["visit"] = st.selectbox(
    "내원 빈도",
    ["매일 통원","주 3~6회","주 1~2회","기타"],
    index=["매일 통원","주 3~6회","주 1~2회","기타"].index(st.session_state["visit"])
)

# ------------------- 버튼: 문진 요약 생성 -------------------
if st.button("① 문진 요약 생성"):
    st.session_state["patient_data"] = build_patient_data()
    prompt_sum = f"다음 환자 문진 내용을 보기 좋게 한국어로 요약:\n{st.session_state['patient_data']}"
    st.session_state["summary"] = call_ai(prompt_sum)

# 항상 표시(있으면)
if st.session_state["summary"]:
    st.subheader("문진 요약")
    st.code(st.session_state["summary"], language="markdown")

# ------------------- 버튼: AI 제안 생성 -------------------
if st.button("② AI 제안 생성"):
    if not st.session_state["patient_data"]:
        st.session_state["patient_data"] = build_patient_data()
    plan_prompt = f"""
너는 한국의 한의원 상담 보조 도우미다. 반드시 한국어로 출력한다.
환자 문진을 보고 JSON 형태의 텍스트만 출력하라.

⚠️ 분류 규칙(증상 기간 onset 반영):
- "일주일 이내" → "급성"
- "1주~1개월" 또는 "1개월~3개월" → "만성"
- "3개월 이상" → "웰니스"

⚠️ 치료 항목 규칙:
- covered는 아래 리스트 중에서만 선택:
  ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
- uncovered는 아래 리스트 중에서만 선택:
  ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]
- 위 리스트에 없는 치료는 절대 covered/uncovered에 넣지 말 것.
- 추가 아이디어는 반드시 extra_suggestions 배열에 적을 것(최소 1개 이상).

⚠️ 주의사항(caution):
- 환자의 병력/복용약 근거로 반드시 한국어로 채우기(빈칸 금지).
- 예: "아토피" 언급 시 항히스타민제/스테로이드 병용 시 졸림·피부자극 등 점검 권장.

출력 JSON 키(영문 고정)과 값(한국어):
classification, duration, covered, uncovered, extra_suggestions, rationale, objective_comment, caution

[환자 문진]
{st.session_state['patient_data']}
"""
    st.session_state["ai_plan"] = call_ai(plan_prompt)

# 항상 표시(있으면)
if st.session_state["ai_plan"]:
    st.subheader("AI 제안 (한국어 JSON)")
    st.code(st.session_state["ai_plan"], language="markdown")

# ------------------- 치료계획 (항상 보이도록 고정) -------------------
st.subheader("③ 최종 치료계획 (의료진 확정)")

st.session_state["cls"] = st.selectbox(
    "질환 분류",
    ["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"],
    index=["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"].index(st.session_state["cls"])
)
st.session_state["period"] = st.selectbox(
    "치료 기간",
    ["1주","2주","3주","4주","1개월 이상"],
    index=["1주","2주","3주","4주","1개월 이상"].index(st.session_state["period"])
)

st.session_state["cov"] = st.multiselect(
    "치료 항목(급여)",
    ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"],
    default=st.session_state["cov"]
)
st.session_state["unc"] = st.multiselect(
    "치료 항목(비급여)",
    ["약침","약침패치","테이핑요법","비급여 맞춤 한약"],
    default=st.session_state["unc"]
)
st.session_state["herb"] = st.radio(
    "맞춤 한약 기간",
    ["선택 안 함","1개월","2개월","3개월"],
    index=["선택 안 함","1개월","2개월","3개월"].index(st.session_state["herb"])
)

# ------------------- 버튼: 최종 결과 생성 -------------------
if st.button("④ 최종 결과 생성"):
    summary = st.session_state.get("summary", "아직 생성되지 않음")
    ai_plan = st.session_state.get("ai_plan", "아직 제안 없음")
    final_text = f"""
=== 환자 문진 요약 ===
{summary}

=== AI 제안 ===
{ai_plan}

=== 최종 치료계획 (의료진 확정) ===
- 분류: {st.session_state['cls']}
- 기간: {st.session_state['period']}
- 급여: {", ".join(st.session_state['cov']) if st.session_state['cov'] else "-"}
- 비급여: {", ".join(st.session_state['unc']) if st.session_state['unc'] else "-"}
- 맞춤 한약: {st.session_state['herb'] if st.session_state['herb']!="선택 안 함" else "-"}
""".strip()
    st.session_state["final_text"] = final_text

# 항상 표시(있으면)
if st.session_state["final_text"]:
    st.subheader("최종 출력")
    st.code(st.session_state["final_text"], language="markdown")
