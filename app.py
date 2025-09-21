import streamlit as st
import requests
import json

# ================== 기본 설정 ==================
st.set_page_config(page_title="숨쉬는한의원 문진 · 치료계획", layout="wide")

API_KEY = st.secrets["API_KEY"]   # 🔑 Streamlit secrets에 저장된 키 불러오기
MODEL = "gemini-1.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# ================== 카테고리 ==================
SYMPTOMS = ["머리","허리","어깨","발/목/뒤꿈치","무릎","손목","허벅지","뒷목 어깻죽지",
            "등","손","손가락","엉덩이/골반","팔꿈치","장단지","손/팔 저림","두통/어지러움",
            "설사","생리통","다리 감각 이상","변비","소화불량","불안 장애","불면","알레르기질환"]

CAUSES = ["사고(운동)","사고(교통사고)","사고(상해)","사고(일상생활)","음식",
          "스트레스","원인모름","기존질환","생활습관 및 환경"]

COVERED_ITEMS = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
UNCOVERED_ITEMS = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]

# ================== 함수 ==================
def call_gemini(prompt):
    res = requests.post(API_URL, json={"contents":[{"role":"user","parts":[{"text":prompt}]}]})
    j = res.json()
    return j.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")

def get_patient():
    return {
        "name": st.session_state.get("name",""),
        "age": st.session_state.get("age",""),
        "bp": st.session_state.get("bp",""),
        "symptoms": st.session_state.get("symptoms",[]),
        "onset": st.session_state.get("onset",""),
        "onset_date": st.session_state.get("onset_date",""),
        "causes": st.session_state.get("causes",[]),
        "history": st.session_state.get("history",""),
        "visit": st.session_state.get("visit","")
    }

# ================== UI ==================
st.title("📝 숨쉬는한의원 문진 · 치료계획 웹앱")

# --- 기본 정보 ---
with st.expander("👤 기본 정보 입력", expanded=True):
    st.text_input("이름", key="name")
    st.number_input("나이", min_value=0, key="age")
    st.text_input("혈압·맥박", key="bp")

# --- 문진 ---
with st.expander("📋 문진", expanded=True):
    st.multiselect("현재 불편한 증상", SYMPTOMS, key="symptoms")
    st.text_input("기타 증상 직접 입력", key="symptom_etc")
    st.selectbox("증상 시작 시점", ["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"], key="onset")
    st.text_input("발병일 (선택)", key="onset_date")
    st.multiselect("증상 원인", CAUSES, key="causes")
    st.text_input("기타 원인 직접 입력", key="cause_etc")
    st.text_area("과거 병력/약물", key="history")
    st.selectbox("내원 빈도", ["매일 통원","주 3~6회","주 1~2회","기타"], key="visit")

# --- 요약 ---
st.subheader("📌 문진 요약")
if st.button("① 요약 생성"):
    p = get_patient()
    etc_sym = st.session_state.get("symptom_etc","")
    etc_cause = st.session_state.get("cause_etc","")
    if etc_sym: p["symptoms"].append(etc_sym)
    if etc_cause: p["causes"].append(etc_cause)

    prompt = f"""
    환자 문진 요약 (진단/처방 금지, 입력 재정리):

    - 이름/나이: {p['name'] or '-'} / {p['age'] or '-'}
    - 혈압/맥박: {p['bp'] or '-'}
    - 주요 증상: {', '.join(p['symptoms']) if p['symptoms'] else '-'}
    - 증상 시작: {p['onset']} {f"({p['onset_date']})" if p['onset_date'] else ''}
    - 원인: {', '.join(p['causes']) if p['causes'] else '-'}
    - 과거 병력/약물: {p['history'] or '-'}
    - 내원 빈도: {p['visit'] or '-'}
    """
    st.session_state["summary"] = call_gemini(prompt)

summary_text = st.session_state.get("summary","아직 생성하지 않았습니다.")
st.markdown(f"<div style='background:#fff;border:1px solid #ddd;border-radius:10px;padding:12px;min-height:120px;white-space:pre-wrap'>{summary_text}</div>", unsafe_allow_html=True)

if st.button("📋 요약 복사"):
    st.session_state["copy_text"] = summary_text
    st.success("요약이 복사되었습니다!")

# --- AI 제안 ---
st.subheader("🤖 AI 제안 (분류/치료/기간/주의사항)")
if st.button("② 제안 생성"):
    p = get_patient()
    prompt = f"""
    너는 숨쉬는한의원 내부 상담 보조 도구다.
    아래 환자 문진을 바탕으로 JSON만 출력하라.

    필수 필드:
    - classification: "급성"|"만성"|"웰니스"
    - duration: "1주"|"2주"|"3주"|"4주"|"1개월 이상"
    - covered: {COVERED_ITEMS} 중 적절한 것 (없으면 빈 배열)
    - uncovered: {UNCOVERED_ITEMS} 중 적절한 것 (없으면 빈 배열)
    - extra_suggestions: 카테고리에 없는 치료법 중 도움이 될만한 추가 제안
    - rationale: 권장 근거
    - objective_comment: 생활습관/재발예방 코멘트
    - caution: 병력/약물 관련 주의사항

    환자 문진:
    {json.dumps(p, ensure_ascii=False, indent=2)}
    """
    raw = call_gemini(prompt)
    try:
        parsed = json.loads(raw[raw.find("{"): raw.rfind("}")+1])
    except:
        parsed = {}

    st.session_state["ai_plan"] = json.dumps(parsed, ensure_ascii=False, indent=2)

ai_text = st.session_state.get("ai_plan","아직 제안이 생성되지 않았습니다.")
st.markdown(f"<div style='background:#fff;border:1px solid #ddd;border-radius:10px;padding:12px;min-height:180px;white-space:pre-wrap;overflow-y:auto'>{ai_text}</div>", unsafe_allow_html=True)

if st.button("📋 AI 제안 복사"):
    st.session_state["copy_text"] = ai_text
    st.success("AI 제안이 복사되었습니다!")

# --- 최종 계획 ---
st.subheader("🩺 최종 치료계획 (의료진 확정)")
st.selectbox("질환 분류", ["급성질환","만성질환","웰니스"], key="cls")
st.selectbox("치료 기간", ["1주","2주","3주","4주","1개월 이상"], key="period")
st.multiselect("치료 항목 (급여)", COVERED_ITEMS, key="covered_sel")
st.multiselect("치료 항목 (비급여)", UNCOVERED_ITEMS, key="uncovered_sel")

if st.button("③ 최종 결과 생성"):
    lines = []
    lines.append("=== 환자 문진 요약 ===")
    lines.append(st.session_state.get("summary","(요약 없음)"))
    lines.append("")
    lines.append("=== AI 제안 ===")
    lines.append(st.session_state.get("ai_plan","(제안 없음)"))
    lines.append("")
    lines.append("=== 최종 치료계획 (의료진 확정) ===")
    lines.append(f"- 분류: {st.session_state['cls']}")
    lines.append(f"- 기간: {st.session_state['period']}")
    lines.append(f"- 급여: {', '.join(st.session_state['covered_sel']) or '-'}")
    lines.append(f"- 비급여: {', '.join(st.session_state['uncovered_sel']) or '-'}")

    st.session_state["final"] = "\n".join(lines)

final_text = st.session_state.get("final","아직 생성하지 않았습니다.")
st.markdown(f"<div style='background:#fff;border:1px solid #ddd;border-radius:10px;padding:12px;min-height:180px;white-space:pre-wrap'>{final_text}</div>", unsafe_allow_html=True)

if st.button("📋 최종계획 복사"):
    st.session_state["copy_text"] = final_text
    st.success("최종 치료계획이 복사되었습니다!")
