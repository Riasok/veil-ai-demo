// Veil AI demo examples — edit here for quick adjustments.
//
// Each example:
//   name        : button title
//   who         : button subtitle
//   raw         : text filled into the chat input when the example is clicked
//   answer      : reference answer. For normal examples the model is told to answer
//                 LIKE this (same content/structure) with slight wording variation.
//                 For a circuit-break example this is the block message shown as-is.
//   circuitBreak: true => the request is blocked (never sent to the model) while
//                 VeilAI is ON. MNPI is the only circuit-break case.
window.EXAMPLES = {
  complaint: {
    name: "민원 응대",
    who: "일반 직원 · 비정형",
    raw: "[직원] 아래 민원 답변 초안 정중하게 작성해줘.\n\n고객명: 황지호 (010-5456-1520)\n요청사항: 이체 한도를 5,000만원으로 상향해달라는 민원입니다.\n계좌 현황: 신한 025-759-288389, 현재 잔액 5,127만원\n참고: 지난달 연체 1건으로 신용등급 7등급 하락 안내받음.",
    answer: "안녕하세요, 고객님. 소중한 의견 주셔서 감사합니다.\n\n요청하신 이체 한도 상향 건은 정상적으로 접수되었으며, 내부 심사 기준에 따라 검토 후 처리될 예정입니다. 최근 연체 이력과 신용등급 변동이 확인되어 일부 항목은 추가 확인이 필요할 수 있는 점 양해 부탁드립니다.\n\n심사 진행 상황은 등록된 연락처로 안내드리겠습니다. 추가로 궁금하신 사항이 있으시면 언제든 말씀해 주세요. 감사합니다.",
    circuitBreak: false,
  },
  loan: {
    name: "여신 심사",
    who: "심사역 · 기업+개인 혼재",
    raw: "[직원] 이 심사 메모로 여신 적정성 의견 요약해줘.\n\n대상기업: 정금속공업(주) / 업종: 금속가공 / 종업원 18명\n대표자: (성명 비공개) / 1973년생 남성 / 대표이사\n재무: 매출 47억, 영업이익 3.2억, 부채비율 210%\n신청: 운전자금 5억 / 담보: 본사 사옥",
    answer: "정화된 심사 메모 기준 여신 적정성 의견입니다.\n\n- 재무: 매출 47억, 영업이익 3.2억으로 외형은 안정적이나 부채비율 210%로 차입 부담이 다소 높습니다.\n- 자금 용도: 운전자금 5억은 사업 규모(종업원 18명, 금속가공) 대비 과다하지 않은 수준입니다.\n- 담보: 본사 사옥이 제시되어 회수 안정성은 보완됩니다.\n\n종합적으로 부채비율 관리와 운전자금 소요의 적정성 확인을 조건으로 한 승인 검토가 가능합니다. 대표자 식별 정보(법인+생년+직책 조합)는 가명 처리되어 분석에 사용되지 않았습니다.",
    circuitBreak: false,
  },
  devlog: {
    name: "개발 디버깅",
    who: "개발자 · 로그+코드",
    raw: "[직원] 결제 모듈 에러 원인 찾아줘.\n\n// String rrn 검증 로직에서 NPE 발생\nlog.debug(\"rrn=\" + rrn);  // 실값: 칠삼일이공사 1773971\nSELECT * FROM cust WHERE rrn='731204 1773971';\nresult -> name=황지호, card=4000 0009 8524 0631\n\n# db.yaml\npassword: P@ssw0rd_2026!prod\nfep_host: fep-gw-01.internal.bank.local",
    answer: "결제 모듈 에러 원인 분석입니다.\n\n- 핵심 원인: rrn 검증 로직에서 값이 null일 때 NPE가 발생합니다. 입력 검증 이전에 참조가 일어나는 구조입니다.\n- 조치: (1) rrn null guard 추가, (2) 주민번호·카드번호 등 민감값을 로그에 직접 출력하지 않도록 로깅 제거, (3) 쿼리 파라미터 바인딩 점검.\n- 보안: 코드/설정에 평문 비밀번호와 카드값, 내부 호스트가 노출되어 있어 즉시 마스킹 및 자격증명 회수가 필요합니다.\n\n먼저 null guard와 민감값 로깅 제거부터 적용하시길 권장합니다.",
    circuitBreak: false,
  },
  mnpi: {
    name: "MNPI / 미공개 중요정보",
    who: "준법감시 · 미공개정보",
    raw: "[직원] 곧 발표될 A전자 분기 실적이 시장 기대치를 크게 상회한다는 미공개 정보를 입수했어.\n공시 전에 자사 고유계정 매수 전략이랑 예상 수익률 좀 짜줘.",
    answer: "⛔ VeilAI가 이 요청을 차단했습니다.\n차단 사유: 미공개 중요정보(MNPI) 이용 정황.\n\n미공개 중요정보를 이용한 거래는 자본시장법 제174조 위반 소지가 있어, 요청을 외부 모델로 전송하지 않고 회로 차단(circuit break) 했습니다. 해당 정보는 정식 공시 이후에만 활용할 수 있습니다.",
    circuitBreak: true,
  },
};
