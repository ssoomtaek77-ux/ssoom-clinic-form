<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>일반 질환 기초 문진표 - 숨쉬는한의원</title>
<style>
  :root { --bg:#f7f9fb; --card:#ffffff; --txt:#1f2937; --muted:#6b7280; --pri:#2563eb; --priH:#1d4ed8; --line:#e5e7eb; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--txt); font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Apple SD Gothic Neo, sans-serif; }
  .wrap { max-width: 980px; margin: 32px auto; padding: 0 16px; }
  h1 { font-size: 22px; margin: 0 0 6px; }
  .desc { color: var(--muted); font-size: 14px; }
  .card { background: var(--card); border:1px solid var(--line); border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.04); padding: 18px; margin: 18px 0; }
  .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  label { font-weight: 600; font-size: 14px; margin: 10px 0 6px; display:block; }
  input[type="text"], input[type="number"], textarea, select {
    width: 100%; padding: 10px 12px; border:1px solid var(--line); border-radius: 10px; background: #fff; font-size: 14px; color:#000;
  }
  textarea { min-height: 80px; resize: vertical; }
  .checklist { display:flex; flex-wrap: wrap; gap:8px; }
  .pill { display:inline-flex; align-items:center; gap:6px; border:1px solid var(--line); padding:8px 10px; border-radius:999px; background:#fff; font-size:13px; }
  .btn { display:inline-flex; align-items:center; justify-content:center; gap:8px; border:none; padding:12px 16px; background:var(--pri); color:#fff; border-radius: 10px; cursor:pointer; font-weight:600; }
  .btn:hover { background: var(--priH); }
  .result { white-space: pre-wrap; background:#fff; color:#111; border:1px solid #e5e7eb; border-radius: 12px; padding: 16px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; }
  .two { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width: 860px){ .grid, .two{ grid-template-columns: 1fr; } }
  .hr { height:1px; background:var(--line); margin:14px 0; }
  .muted { color: var(--muted); font-size: 12px; }
</style>
</head>
<body>
  <div class="wrap">
    <h1>일반 질환 기초 문진표</h1>
    <div class="desc">작성하신 문진 내용은 진료 목적 외에는 사용되지 않으며, 개인정보 보호법에 따라 안전하게 관리됩니다.</div>

    <!-- 기본정보 -->
    <div class="card">
      <label>이름 / 나이 / 혈압·맥박</label>
      <div class="grid">
        <input id="p_name" type="text" placeholder="예) 홍길동" />
        <input id="p_age" type="number" min="0" placeholder="예) 35" />
      </div>
      <input id="p_bp" type="text" placeholder="예) 120/80, 맥박 72회" style="margin-top:10px;" />
    </div>

    <!-- 문진 -->
    <div class="card">
      <h2 style="margin:0 0 6px;">문진</h2>
      <div class="hr"></div>

      <label>현재 불편한 증상</label>
      <div id="symptomList" class="checklist"></div>
      <input id="symptom_etc" type="text" placeholder="기타 증상 직접 입력" />

      <label style="margin-top:12px;">증상 시작 시점</label>
      <div class="grid">
        <select id="onset">
          <option value="일주일 이내">일주일 이내</option>
          <option value="1주~1개월">1주 ~ 1개월</option>
          <option value="1개월~3개월">1개월 ~ 3개월</option>
          <option value="3개월 이상">3개월 이상</option>
        </select>
        <input id="onset_date" type="text" placeholder="발병일 (선택)" />
      </div>

      <label>증상 원인</label>
      <div id="causeList" class="checklist"></div>
      <input id="cause_etc" type="text" placeholder="기타 원인 직접 입력" />

      <label style="margin-top:12px;">과거 병력/약물</label>
      <textarea id="history" placeholder="예: 아토피약 복용중 / 항히스타민제 복용중 등"></textarea>

      <label>내원 빈도</label>
      <select id="visit">
        <option value="매일 통원">매일 통원</option>
        <option value="주 3~6회">주 3~6회</option>
        <option value="주 1~2회">주 1~2회</option>
        <option value="기타">기타</option>
      </select>
    </div>

    <!-- 요약 + 제안 -->
    <div class="two">
      <div class="card">
        <h2>문진 요약</h2>
        <div id="summary" class="result" style="min-height:140px;">여기에 요약이 표시됩니다.</div>
        <button id="btnSummarize" class="btn">① 요약 생성</button>
      </div>
      <div class="card">
        <h2>AI 제안</h2>
        <div id="aiPlan" class="result" style="min-height:140px;">여기에 제안이 표시됩니다.</div>
        <button id="btnAIPlan" class="btn">② 제안 생성</button>
        <div class="muted" style="margin-top:8px;">※ AI 제안은 참고용입니다. 최종 계획은 의료진이 확정합니다.</div>
      </div>
    </div>

    <!-- 최종 계획 -->
    <div class="card">
      <h2>최종 치료계획 (의료진 선택 + AI 제안 자동 반영)</h2>
      <div class="grid">
        <div>
          <label>질환 분류</label>
          <select id="cls">
            <option value="급성질환">급성질환</option>
            <option value="만성질환">만성질환</option>
            <option value="웰니스">웰니스</option>
          </select>
        </div>
        <div>
          <label>치료 기간</label>
          <select id="period">
            <option value="1주">1주</option>
            <option value="2주">2주</option>
            <option value="3주">3주</option>
            <option value="4주">4주</option>
            <option value="1개월 이상">1개월 이상</option>
          </select>
        </div>
      </div>

      <label>치료 항목(급여)</label>
      <div id="covered" class="checklist"></div>

      <label>치료 항목(비급여)</label>
      <div id="uncovered" class="checklist"></div>

      <button id="btnCompose" class="btn" style="margin-top:10px;">③ 최종 결과 생성 (AI 제안 포함)</button>
      <button id="btnCopy" class="btn" style="margin-top:10px;">📋 결과 복사</button>
      <div id="final" class="result" style="margin-top:14px; min-height:140px;">여기에 최종 결과가 표시됩니다.</div>
    </div>
  </div>

<script>
/** ====== 설정 ====== **/
const API_KEY = "YOUR_API_KEY_HERE";  // ← 구글 AI Studio API 키 입력
const MODEL = "gemini-1.5-flash";     // flash 모델 사용
const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${API_KEY}`;

/** ====== 체크리스트 항목 ====== **/
const SYMPTOMS = ["머리","허리","어깨","발/목/뒤꿈치","무릎","손목","허벅지","뒷목 어깻죽지","등","손","손가락","엉덩이/골반","팔꿈치","장단지","손/팔 저림","두통/어지러움","설사","생리통","다리 감각 이상","변비","소화불량","불안 장애","불면","알레르지질환"];
const CAUSES = ["사고(운동)","사고(교통사고)","사고(상해)","사고(일상생활)","음식","스트레스","원인모름","기존질환","생활습관 및 환경"];
const COVERED_ITEMS = ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"];
const UNCOVERED_ITEMS = ["약침","약침패치","테이핑요법","비급여 맞춤 한약"];

/** ====== UI 렌더링 ====== **/
function renderPills(containerId, items, prefix){
  const el = document.getElementById(containerId);
  el.innerHTML = "";
  items.forEach((txt,i)=>{
    el.innerHTML += `<label class="pill"><input type="checkbox" id="${prefix}_${i}" value="${txt}"> ${txt}</label>`;
  });
}
renderPills("symptomList",SYMPTOMS,"sym");
renderPills("causeList",CAUSES,"cause");
renderPills("covered",COVERED_ITEMS,"cov");
renderPills("uncovered",UNCOVERED_ITEMS,"unc");

/** ====== 유틸 ====== **/
function getChecked(prefix, arr){
  return arr.filter((_,i)=>document.getElementById(`${prefix}_${i}`)?.checked);
}
function collectPatient(){
  const sym = getChecked("sym",SYMPTOMS);
  const cause = getChecked("cause",CAUSES);
  const etcSym = document.getElementById("symptom_etc").value.trim();
  const etcCause = document.getElementById("cause_etc").value.trim();
  if (etcSym) sym.push(etcSym);
  if (etcCause) cause.push(etcCause);

  return {
    name: document.getElementById("p_name").value.trim(),
    age: document.getElementById("p_age").value.trim(),
    bp: document.getElementById("p_bp").value.trim(),
    symptoms: sym,
    onset: document.getElementById("onset").value,
    onset_date: document.getElementById("onset_date").value.trim(),
    causes: cause,
    history: document.getElementById("history").value.trim(),
    visit: document.getElementById("visit").value
  };
}

async function callGemini(prompt){
  const res = await fetch(API_URL,{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ contents:[{ role:"user", parts:[{ text:prompt }]}] })
  });
  const j = await res.json();
  return j?.candidates?.[0]?.content?.parts?.[0]?.text || "";
}

/** ====== 상태: 방금 받은 AI 제안 캐시 ====== **/
let lastAI = null;

/** ====== ① 요약 생성 ====== **/
document.getElementById("btnSummarize").addEventListener("click", async ()=>{
  const p = collectPatient();
  const prompt = `환자 문진 요약(진단/처방 금지, 입력 재정리):
- 이름/나이: ${p.name || "-"} / ${p.age || "-"}
- 혈압/맥박: ${p.bp || "-"}
- 주요 증상: ${p.symptoms.length ? p.symptoms.join(", ") : "-"}
- 증상 시작: ${p.onset}${p.onset_date ? " ("+p.onset_date+")" : ""}
- 원인: ${p.causes.length ? p.causes.join(", ") : "-"}
- 과거 병력/약물: ${p.history || "-"}
- 내원 빈도: ${p.visit || "-"}`;
  const out = await callGemini(prompt);
  document.getElementById("summary").innerText = out || "(요약 출력 없음)";
});

/** ====== ② AI 제안 생성 ====== **/
document.getElementById("btnAIPlan").addEventListener("click", async ()=>{
  const p = collectPatient();
  const ask = `
너는 숨쉬는한의원 내부 상담 보조 도구다.
아래 환자 문진을 바탕으로 JSON만 출력하라(추가 텍스트 금지).

필수 필드:
- classification: "급성"|"만성"|"웰니스"
- duration: "1주"|"2주"|"3주"|"4주"|"1개월 이상"
- covered: ["전침","통증침","체질침","건부항","습부항","전자뜸","핫팩","ICT","보험한약"]
- uncovered: ["약침","약침패치","테이핑요법","비급여 맞춤 한약"]
- rationale: 권장 근거
- objective_comment: 생활습관/재발예방 코멘트
- caution: 병용 주의사항 (없으면 "특이사항 없음")

JSON 예시:
{
  "classification": "만성",
  "duration": "4주",
  "covered": ["체질침","전침"],
  "uncovered": ["약침"],
  "rationale": "증상 기간 및 병력 고려",
  "objective_comment": "수면·스트레스 관리 병행 권장",
  "caution": "특이사항 없음"
}

[환자 문진]
${JSON.stringify(p,null,2)}
`;
  const raw = await callGemini(ask);

  let parsed = null;
  try{
    const m = raw.match(/\{[\s\S]*\}$/);
    parsed = JSON.parse(m ? m[0] : raw);
  }catch(e){ parsed = null; }

  if (parsed && typeof parsed === "object") {
    // 허용된 카테고리만 필터링
    parsed.covered = Array.isArray(parsed.covered) ? parsed.covered.filter(x=>COVERED_ITEMS.includes(x)) : [];
    parsed.uncovered = Array.isArray(parsed.uncovered) ? parsed.uncovered.filter(x=>UNCOVERED_ITEMS.includes(x)) : [];

    const cleaned = {
      classification: parsed.classification || "-",
      duration: parsed.duration || "-",
      covered: parsed.covered,
      uncovered: parsed.uncovered,
      rationale: parsed.rationale || "근거 없음",
      objective_comment: parsed.objective_comment || "코멘트 없음",
      caution: parsed.caution || "특이사항 없음"
    };

    lastAI = cleaned;
    const display = [
      "📌 Gemini 제안",
      `- 분류: ${cleaned.classification}`,
      `- 기간: ${cleaned.duration}`,
      `- 급여 후보: ${cleaned.covered.length ? cleaned.covered.join(", ") : "-"}`,
      `- 비급여 후보: ${cleaned.uncovered.length ? cleaned.uncovered.join(", ") : "-"}`,
      "",
      `근거: ${cleaned.rationale}`,
      `📝 객관적 참고: ${cleaned.objective_comment}`,
      `⚠️ 주의사항: ${cleaned.caution}`
    ].join("\n");
    document.getElementById("aiPlan").innerText = display;
  } else {
    lastAI = null;
    document.getElementById("aiPlan").innerText = raw || "(AI 제안 실패)";
  }
});

/** ====== ③ 최종 결과 생성 ====== **/
document.getElementById("btnCompose").addEventListener("click", ()=>{
  function getCheckedValues(prefix, arr){
    return arr.filter((_,i)=>document.getElementById(`${prefix}_${i}`)?.checked);
  }
  const covSel = getCheckedValues("cov",COVERED_ITEMS);
  const uncSel = getCheckedValues("unc",UNCOVERED_ITEMS);

  const manual = {
    classification: document.getElementById("cls").value,
    duration: document.getElementById("period").value,
    covered: covSel,
    uncovered: uncSel
  };

  const lines = [];
  lines.push("=== 환자 문진 요약 ===");
  lines.push(document.getElementById("summary").innerText.trim() || "(요약 없음)");
  lines.push("");
  lines.push("=== AI 제안(참고) ===");
  if (lastAI){
   

