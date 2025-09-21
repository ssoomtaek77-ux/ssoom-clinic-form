import streamlit as st
import google.generativeai as genai
import json
from typing import Optional

# ========================
# 페이지 / 키 설정
# ========================
st.set_page_config(page_title="일반 질환 기초 문진표", page_icon="🩺", layout="wide")

API_KEY = st.secrets.get("GOOGLE_API_KEY")
if not API_KEY:
    st.error("관리자: Streamlit Secrets에 GOOGLE_API_KEY를 설정하세요.")
    st.stop()

genai.configure(api_key=API_KEY)
MODEL = "gemini-1.5-flash"  # 안정 테스트용: quota 친화적

# ========================
# 유틸: AI 호출
# ========================
def call_ai_text(prompt: str, max_output_tokens: int = 512, temperature: float = 0.2) -> str:
    try:
        model = genai.GenerativeModel(MODEL)
        # generation_config 옵션은 모델/SDK 버전에 따라 다를 수 있으니 최소 파라미터만 사용
        res = model.generate_content(prompt, generation_config={"max_output_tokens": max_output_tokens, "temperature": temperature})
        # SDK의 반환 형태에 따라 속성 접근
        text = getattr(res, "text", None)
        if not text:
            # fallback: try nested structure
            try:
                text = res._result.response.candidates[0].content.parts[0].text
            except Exception:
                text = ""
        return text or ""
    except Exception as e:
        return f"❌ AI 호출 오류: {e}"

def call_ai_json(prompt: str, max_output_tokens: int = 512, temperature: float = 0.2) -> Optional[dict]:
    raw = call_ai_text(prompt, max_output_tokens=max_output_tokens, temperature=temperature)
    if not raw:
        return None
    # Try to extract JSON object from raw text
    try:
        # Common patterns: plain JSON, or fenced code block
        import re
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            return json.loads(m.group(0))
        # last attempt: if raw itself is JSON-like
        return json.loads(raw)
    except Exception:
        # If parsing fails, return as error wrapper
        return {"_raw_text": raw}

# ========================
# 레이아웃: 왼쪽 입력 / 오른쪽 결과 (wide)
# ========================
st.title("일반 질환 기초 문진표 · 숨쉬는한의원")
col1, col2 = st.columns([1, 1.2])

with col1:
    st.header("환자 입력")
    with st.form("patient_form", clear_on_submit=False):
        name = st.text_input("이름")
        age = st.number_input("나이", min_value=0, max_value=120, value=30)
        bp = st.text_input("혈압/맥박 (예: 120/80, 맥박 72)")

        st.markdown("**1) 현재 불편한 증상**")
        symptoms = st.multiselect("증상 선택 (체크)", [
            "머리","허리","어깨","발/목/뒤꿈치","무릎","손목","허벅지","뒷목 어깻죽지",
            "등","손","손가락","엉덩이/골반","팔꿈치","장단지","손/팔 저림",
            "두통/어지러움","설사","생리통","다리 감각 이상","변비","소화불량",
            "불안 장애","불면","알레르지질환"
        ])
        symptom_etc = st.text_input("기타 증상 (자유서술)")

        st.markdown("**2) 증상 시작 시점**")
        onset = st.selectbox("증상 시작", ["일주일 이내", "1주~1개월", "1개월~3개월", "3개월 이상"])
        onset_date = st.text_input("발병일 (선택) — 예: 2025-09-15")

        st.markdown("**3) 증상 원인**")
        causes = st.multiselect("원인 선택", [
            "사고(운동)","사고(교통사고)","사고(상해)","사고(일상생활)",
            "음식","스트레스","원인모름","기존질환","생활습관 및 환경"
        ])
        cause_disease = st.text_input("기존질환 (병명 입력, 선택)")
        cause_lifestyle = st.text_input("생활습관/환경 (선택)")

        st.markdown("**4) 과거 병력 / 현재 복용 약물 / 치료 상태**")
        history = st.text_area("예: 아토피약 복용중 / 항히스타민제 복용 / 물리치료 중 등")

        st.markdown("**5) 내원 빈도**")
        visit = st.selectbox("내원 빈도", ["매일 통원","주 3~6회","주 1~2회","기타"])
        visit_etc = st.text_input("기타(선택)")

        generate_button = st.form_submit_button("저장 (입력 반영)")

    # 버튼들: 요약/AI 제안 별도 호출
    st.markdown("---")
    if st.button("① 문진 요약 생성 (AI)"):
        st.session_state._do_summary = True
    if st.button("② AI 제안 생성 (분류/치료/주의사항)"):
        st.session_state._do_plan = True

with col2:
    st.header("요약 / AI 제안 / 치료계획")
    # Build patient_data string from current fields (even if form not submitted)
    def make_patient_text():
        s = symptoms[:] if symptoms else []
        if symptom_etc and symptom_etc.strip():
            s.append(symptom_etc.strip())
        causes_list = causes[:] if causes else []
        if cause_disease and cause_disease.strip():
            causes_list.append(f"기존질환:{cause_disease.strip()}")
        if cause_lifestyle and cause_lifestyle.strip():
            causes_list.append(f"생활습관:{cause_lifestyle.strip()}")
        visit_display = visit_etc if visit == "기타" and visit_etc else visit
        return (
            f"이름: {name or '-'}\n"
            f"나이: {age}\n"
            f"혈압/맥박: {bp or '-'}\n"
            f"증상: {', '.join(s) if s else '-'}\n"
            f"증상 시작: {onset}" + (f" (발병일: {onset_date})" if onset_date else "") + "\n"
            f"원인: {', '.join(causes_list) if causes_list else '-'}\n"
            f"과거/복용약/치료: {history or '-'}\n"
            f"내원 빈도: {visit_display or '-'}\n"
        )

    patient_text = make_patient_text()

    # 문진 요약 출력
    st.subheader("📌 문진 요약")
    if st.session_state.get("_do_summary", False):
        with st.spinner("문진 요약 생성 중..."):
            prompt = f"다음 환자 문진을 보기 좋게 간결히 요약하라. SOAP 형태 금지.\n\n{patient_text}"
            summary_out = call_ai_text(prompt, max_output_tokens=400)
            st.session_state._summary = summary_out
            st.session_state._do_summary = False
    summary_to_show = st.session_state.get("_summary", "(아직 생성되지 않음. '① 문진 요약 생성'을 눌러주세요.)")
    st.text_area("문진 요약", summary_to_show, height=160)

    # AI 제안 (JSON)
    st.subheader("🤖 AI 제안 (분류/치료 항목/기간/주의사항)")
    if st.session_state.get("_do_plan", False):
        with st.spinner("AI 제안 생성 중..."):
            plan_prompt = f"""
너는 한의원 상담 보조 도우미다. 아래 환자 문진을 보고 JSON만 출력하라.
필수 필드:
- classification: \"급성\"|\"만성\"|\"웰니스\"
- duration: \"1주\"|\"2주\"|\"3주\"|\"4주\"|\"1개월 이상\"
- covered: 급여 후보 배열 (전침, 통증침 등)
- uncovered: 비급여 후보 배열
- rationale: 권장 근거
- objective_comment: 생활습관/재발예방 등
- caution: 환자 병력/약물 병행 시 주의사항 (빈칸 금지)

환자 문진:
{patient_text}
"""
            raw_json = call_ai_json(plan_prompt, max_output_tokens=600)
            # parse fallback
            if raw_json is None:
                st.session_state._ai_json = {"error": "AI 응답 없음"}
            else:
                # if raw_json is a dict with _raw_text, keep it separately
                if isinstance(raw_json, dict) and "_raw_text" in raw_json:
                    st.session_state._ai_json = {"parse_error": True, "raw": raw_json["_raw_text"]}
                else:
                    st.session_state._ai_json = raw_json
            st.session_state._do_plan = False

    ai_json = st.session_state.get("_ai_json", None)
    if ai_json is None:
        st.info("AI 제안은 '② AI 제안 생성'을 눌러 생성하세요.")
    else:
        st.json(ai_json)

    # 자동 보완: caution fallback and auto-note for '아토피' in history
    def ai_caution_fallback(ai_json_obj):
        if not ai_json_obj:
            return "특이사항 없음 (AI 출력 누락)"
        if isinstance(ai_json_obj, dict):
            c = ai_json_obj.get("caution") or ""
            if not c.strip():
                c = "특이사항 없음 (AI 출력 누락)"
            # if patient history mentions 아토피, append safety tip
            if "아토피" in (history or "") and "아토피" not in c:
                c += "\n(자동 안내) 아토피 관련 약물 복용 가능성 — 항히스타민제/스테로이드 병용 시 졸림·피로/피부 자극 등 관찰 필요."
            return c
        return "특이사항 없음 (AI 출력 누락)"

    st.markdown("---")
    st.subheader("🩺 최종 치료계획 (의료진 확정) — 항상 보임")
    # These controls are always visible
    cls = st.selectbox("질환 분류(의료진 선택)", ["급성질환(10~14일)","만성질환(15일~3개월)","웰니스(3개월 이상)"])
    period = st.selectbox("치료 기간(의료진 선택)", ["1주","2주","3주","4주","1개월 이상"])

    covered_options = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
    cov = st.multiselect("치료 항목(급여) — 선택", covered_options)

    uncovered_options = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]
    unc = st.multiselect("치료 항목(비급여) — 선택", uncovered_options)
    herb = st.selectbox("비급여 맞춤 한약 기간", ["선택 안 함","1개월","2개월","3개월"])

    if st.button("③ 최종 결과 생성 (AI 제안 포함, 의료진 확정)"):
        lines = []
        lines.append("=== 환자 문진 요약 ===")
        lines.append(summary_to_show if summary_to_show else "(요약 미생성)")
        lines.append("")
        lines.append("=== AI 제안 (참고) ===")
        if ai_json:
            # present caution fallback
            caution_text = ai_caution_fallback(ai_json)
            # show core fields if exist
            if isinstance(ai_json, dict):
                lines.append(f"- 분류(제안): {ai_json.get('classification','-')}")
                lines.append(f"- 권장 기간(제안): {ai_json.get('duration','-')}")
                lines.append(f"- 급여 후보(제안): {', '.join(ai_json.get('covered',[])) if ai_json.get('covered') else '-'}")
                lines.append(f"- 비급여 후보(제안): {', '.join(ai_json.get('uncovered',[])) if ai_json.get('uncovered') else '-'}")
                lines.append(f"- 근거: {ai_json.get('rationale','-')}")
                lines.append(f"- 객관 코멘트: {ai_json.get('objective_comment','-')}")
                lines.append(f"- 주의사항(보완): {caution_text}")
            else:
                lines.append(str(ai_json))
        else:
            lines.append("(AI 제안 없음)")

        lines.append("")
        lines.append("=== 최종 치료계획 (의료진 확정) ===")
        lines.append(f"- 분류(의료진): {cls} {'(AI:'+ (ai_json.get('classification') if isinstance(ai_json, dict) else '-') +')' if isinstance(ai_json, dict) else ''}")
        lines.append(f"- 기간(의료진): {period} {'(AI:'+ (ai_json.get('duration') if isinstance(ai_json, dict) else '-') +')' if isinstance(ai_json, dict) else ''}")
        lines.append(f"- 급여(의료진): {', '.join(cov) if cov else '-'} {('(AI 후보: '+', '.join(ai_json.get('covered'))+')') if isinstance(ai_json, dict) and ai_json.get('covered') else ''}")
        unc_display = unc[:] if unc else []
        if herb != "선택 안 함":
            unc_display.append(f"비급여 맞춤 한약({herb})")
        lines.append(f"- 비급여(의료진): {', '.join(unc_display) if unc_display else '-'} {('(AI 후보: '+', '.join(ai_json.get('uncovered'))+')') if isinstance(ai_json, dict) and ai_json.get('uncovered') else ''}")
        lines.append("")
        lines.append("※ 본 출력은 참고용입니다. 최종 판단은 의료진이 합니다.")

        st.text_area("최종 출력", "\n".join(lines), height=420)
