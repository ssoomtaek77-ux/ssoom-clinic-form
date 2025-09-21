import streamlit as st
import requests
import json

# ====== 설정 ====== #
st.set_page_config(page_title="일반 질환 기초 문진표 · 숨쉬는한의원", layout="wide")

API_KEY = st.secrets["API_KEY"]  # ← Streamlit secrets에 저장한 Google API Key
TEXT_MODEL = "gemini-1.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{TEXT_MODEL}:generateContent?key={API_KEY}"

SYMPTOMS = ["머리","허리","어깨","발/목/뒤꿈치","무릎","손목","허벅지","뒷목 어깻죽지","등","손","손가락",
            "엉덩이/골반","팔꿈치","장단지","손/팔 저림","두통/어지러움","설사","생리통","다리 감각 이상",
            "변비","소화불량","불안 장애","불면","알레르지질환"]
CAUSES = ["사고(운동)","사고(교통사고)","사고(상해)","사고(일상생활)","음식","스트레스","원인모름","기존질환","생활습관 및 환경"]
COVERED_ITEMS = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
UNCOVERED_ITEMS = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]

# ====== 유틸 ====== #
def call_gemini(prompt: str):
    res = requests.post(
        API_URL,
        headers={"Content-Type": "application/json"},
        json={"contents":[{"role":"user","parts":[{"text":prompt}]}]}
    )
    if res.status_code != 200:
        return f"Error {res.status_code}: {res.text}"
    j = res.json()
    return j.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")

def copy_button(text, key):
    st.code(text, language="markdown")
    st.button("📋 복사하기", key=key, on_click=lambda: st.session_state.update({"_copy": text}))

# ====== 입력 ====== #
st.title("일반 질환 기초 문진표")
st.caption("작성하신 문진 내용은 진료 목적 외에는 사용되지 않으며, 개인정보 보호법에 따라 안전하게 관리됩니다.")

col1, col2 = st.columns(2)
with col1:
    name = st.text_input("이름")
    age = st.number_input("나이", min_value=0, step=1)
with col2:
    bp = st.text_input("혈압·맥박", placeholder="예: 120/80, 맥박 72회")

symptoms = st.multiselect("현재 불편한 증상", SYMPTOMS)
symptom_etc = st.text_input("기타 증상 직접 입력")

col3, col4 = st.columns(2)
with col3:
    onset = st.selectbox("증상 시작 시점", ["일주일 이내","1주~1개월","1개월~3개월","3개월 이상"])
with col4:
    onset_date = st.text_input("발병일 (선택)")

causes = st.multiselect("증상 원인", CAUSES)
cause_etc = st.text_input("기타 원인 직접 입력")

history = st.text_area("과거 병력/약물")
visit = st.selectbox("내원 빈도", ["매일 통원","주 3~6회","주 1~2회","기타"])

# ====== AI 처리 ====== #
patient_info = {
    "name": name, "age": age, "bp": bp,
    "symptoms": symptoms + ([symptom_etc] if symptom_etc else []),
    "onset": onset, "onset_date": onset_date,
    "causes": causes + ([cause_etc] if cause_etc else []),
    "history": history, "visit": visit
}

# --- ① 요약 ---
if st.button("① 문진 요약 생성"):
    prompt = f"""환자 문진 요약(진단/처방 금지, 입력 재정리):
- 이름/나이: {patient_info['name'] or '-'} / {patient_info['age'] or '-'}
- 혈압/맥박: {patient_info['bp'] or '-'}
- 주요 증상: {', '.join(patient_info['symptoms']) if patient_info['symptoms'] else '-'}
- 증상 시작: {patient_info['onset']} ({patient_info['onset_date']})
- 원인: {', '.join(patient_info['causes']) if patient_info['causes'] else '-'}
- 과거 병력/약물: {patient_info['history'] or '-'}
- 내원 빈도: {patient_info['visit']}"""
    summary = call_gemini(prompt)
    st.subheader("문진 요약")
    copy_button(summary, "copy_summary")

# --- ② AI 제안 ---
if st.button("② AI 제안 생성"):
    ask = f"""
너는 숨쉬는한의원 내부 상담 보조 도구다.
아래 환자 문진을 바탕으로 반드시 JSON만 출력하라.
⚠️ 주의: 반드시 아래 카테고리 안에서만 추천하라. (벗어나면 잘못된 출력임)

분류: "급성질환"|"만성질환"|"웰니스"
치료 기간: "1주"|"2주"|"3주"|"4주"|"1개월 이상"
급여: {COVERED_ITEMS}
비급여: {UNCOVERED_ITEMS}

필드:
- classification
- duration
- covered
- uncovered
- rationale
- objective_comment
- caution

[환자 문진]
{json.dumps(patient_info, ensure_ascii=False, indent=2)}
"""
    raw = call_gemini(ask)
    st.subheader("AI 제안 (JSON 원본)")
    copy_button(raw, "copy_ai")

# --- ③ 최종 계획 ---
cls = st.selectbox("질환 분류", ["급성질환","만성질환","웰니스"])
period = st.selectbox("치료 기간", ["1주","2주","3주","4주","1개월 이상"])
cov_sel = st.multiselect("치료 항목(급여)", COVERED_ITEMS)
unc_sel = st.multiselect("치료 항목(비급여)", UNCOVERED_ITEMS)

if st.button("③ 최종 결과 생성"):
    lines = []
    lines.append("=== 환자 문진 요약 ===")
    lines.append(st.session_state.get("_copy","(요약 없음)"))
    lines.append("")
    lines.append("=== 최종 치료계획 (의료진 확정) ===")
    lines.append(f"- 분류: {cls}")
    lines.append(f"- 기간: {period}")
    lines.append(f"- 급여: {', '.join(cov_sel) if cov_sel else '-'}")
    lines.append(f"- 비급여: {', '.join(unc_sel) if unc_sel else '-'}")
    lines.append("")
    lines.append("※ 고지: 본 계획은 의료진의 임상 판단과 환자 동의에 따라 확정되었으며, AI 출력은 참고자료로만 활용되었습니다.")

    final_out = "\n".join(lines)
    st.subheader("최종 결과")
    copy_button(final_out, "copy_final")
