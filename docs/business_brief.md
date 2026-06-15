# AI 창업: Veil AI

## 한 줄 피치

**Veil AI는 한국 금융기관이 외부·하이브리드 LLM을 안전하게 쓰도록 돕는 AI 보안 게이트웨이다.** 개인정보·신용정보·내부 기밀을 통제하고, 모델 사용 권한과 감사 로그, 규제 증빙까지 함께 관리한다.

조금 더 풀어 말하면, 금융기관이 ChatGPT, Claude, EXAONE, Llama, 내부 모델을 업무에 붙일 때 데이터와 모델 사이에 들어가는 **control layer**다.

## 핵심 논지

이제 문제는 은행이 생성형 AI를 쓸지 말지가 아니다. 이미 쓰기 시작했다. 진짜 문제는 개인정보·신용정보·망분리·감사·AI 거버넌스 규제를 어기지 않으면서, 실제 업무 데이터에 frontier model과 multi-model AI를 어떻게 붙일 것인가다.

이 지점에서 은행 데이터와 LLM 사이에 새로운 인프라가 필요해진다.

- 민감정보가 외부 모델로 나가기 전에 탐지·마스킹한다.
- 부서·직무·채널·모델별 사용 가능 범위를 정책으로 통제한다.
- 프롬프트, 파일, 모델 호출, 에이전트 액션, 응답, 승인, 예외를 모두 기록한다.
- 보안·준법·CISO 승인·향후 AI 감사에 필요한 증빙을 만든다.

Veil을 단순한 “PII 마스킹 툴”로 잡으면 너무 작고 이미 경쟁이 많다. 더 맞는 포지션은 **금융 AI control plane**이다. 마스킹은 핵심 모듈 중 하나지만, 더 큰 가치는 거버넌스, 모델 라우팅, 감사 로그, 에이전트 통제에 있다.

## 인터뷰에서 얻은 신호

신한은행 개발자 인터뷰에서 중요한 시사점이 몇 가지 나왔다.

1. **내부 업무 PC에서는 외부 AI를 직접 쓰기 어렵다.** 금융권은 망분리가 되어 있어 업무 PC에서는 ChatGPT나 Claude 같은 외부 AI를 쓰지 못하고, 인터넷 PC에서 별도로 사용한다.

2. **외부 AI 사용은 제품화된 통제보다 정책에 더 가깝다.** 회사정보와 개인정보를 외부 AI에 넣지 말라는 정책은 있지만, 실제 사용은 사람이 조심해서 처리하는 구조에 가깝다. 이 지점에서 shadow AI와 수작업 복사 문제가 생긴다.

3. **내부 AI agent는 있지만 품질이 아직 약하다.** 내부망에 자체 agent가 존재하지만, 체감 성능은 “2024년 GPT 느낌”에 가깝다고 했다. 즉 내부 모델만으로 frontier model 수요를 완전히 대체하기 어렵다.

4. **에이전트 모니터링 자체는 어렵지 않다.** LangSmith, Langfuse 같은 도구로 LLM application을 추적하는 것은 가능하다. 따라서 단순 observability만으로는 차별점이 약하다.

5. **일반적인 민감정보 보호와 사용 내역 관리는 이미 존재한다.** 개인정보·민감정보 보호 솔루션은 대체로 제공되고 있고, 사용 내역 관리도 일반 솔루션이나 오픈소스에서 가능하다는 답변을 받았다. 명확한 니즈는 “정말 높은 신뢰도로 탐지·차단할 수 있는가”에 있다.

결론은 분명하다. **기회는 있지만, 초기 아이디어는 너무 넓다.** 은행은 이 카테고리를 필요로 하지만, 또 하나의 일반 마스킹 API나 대시보드를 살 이유는 약하다. Veil은 더 날카로운 wedge가 필요하다.

## 문제

은행이 생성형 AI를 붙이고 싶어 하는 업무에는 민감정보가 자연스럽게 섞인다.

| 업무 | 민감정보 리스크 | 비즈니스 가치 |
| --- | --- | --- |
| 직원용 규정·상품 copilot | 고객정보, 내부 규정, 상품 정책 | 응대 속도, 교육기간 단축 |
| 여신·대출 문서 보조 | 신용정보, 재무제표, 심사 메모 | 심사 시간 단축 |
| 자산관리·리서치 요약 | 고객 포트폴리오, MNPI, 투자 의견 | advisor follow-up 단축 |
| 개발·운영 copilot | 소스코드, 인프라 로그, 장애 정보 | 개발 생산성, 디버깅 속도 |
| Agentic AI workflow | API 호출, 도구 권한, 데이터 조합 | 단순 챗봇을 넘어선 자동화 |

어려운 점은 이름이나 주민번호 하나를 마스킹하는 데서 끝나지 않는다. 실제 업무 데이터의 민감정보는 훨씬 복잡하다.

- 한국어 이름, 계좌번호, 주민등록번호, 전화번호, 주소
- 신용점수, 담보 정보, 대출 이력, 거래 내역
- 내부 정책, 상품 가격, 리스크 메모, 보안 로그
- 여러 프롬프트·도구 호출·검색 문서가 합쳐지며 재구성되는 정보
- 에이전트가 여러 내부 시스템을 호출하며 조합하는 데이터

직원이나 AI agent가 이 데이터를 외부 모델로 보내면, 은행은 무엇이 전송됐는지, 무엇이 마스킹됐는지, 어떤 모델이 쓰였는지, 누가 승인했는지, 응답에서 새로운 리스크가 생겼는지를 증명할 수 있어야 한다.

## 왜 지금인가

몇 가지 흐름이 동시에 온다.

- **금융권 AI 도입이 빨라지고 있다.** KB, NH농협, 우리은행, IBK, KIC, 금융결제원 등에서 AI 플랫폼 또는 LLM 관련 프로젝트가 공개적으로 나오고 있다.
- **시장은 단일 모델이 아니라 multi-model로 간다.** 은행은 내부 모델 하나만 쓰지 않는다. 내부 모델, EXAONE, OpenAI, Claude, Llama, 도메인 모델을 업무별로 섞어 쓰려 한다.
- **규제는 더 구체화되고 있다.** AI 기본법, 금융권 AI 거버넌스, 망분리 개선, 금융 AI 가이드라인은 모두 통제와 증빙의 필요성을 키운다.
- **Agentic AI가 새로운 리스크를 만든다.** AI가 API를 호출하고, 문서를 검색하고, 보고서를 쓰고, 업무를 실행하기 시작하면 기존 문서 중심 DLP만으로는 부족하다.

한 줄 요약: **AI 도입과 AI 규제가 동시에 빨라지는 시점이기 때문에, control layer가 예산을 받을 가능성이 커진다.**

## 제품 방향

Veil은 일반 익명화 SaaS가 아니라 **금융권용 AI 보안 게이트웨이**로 포지셔닝해야 한다.

핵심 모듈은 네 가지다.

1. **민감정보 탐지와 마스킹**
   - 한국 금융권 PII, 신용정보, 내부 기밀 탐지
   - 프롬프트, 파일, RAG 검색 결과, API payload, 모델 응답 스캔
   - 업무상 복원이 필요한 경우 reversible tokenization 지원

2. **모델·정책 게이트웨이**
   - OpenAI, Anthropic, EXAONE, HyperCLOVA, Llama, 내부 모델 라우팅
   - 부서·직무·역할별 사용 정책 적용
   - 고위험 프롬프트, 파일, 모델, 목적지에 대해 차단 또는 승인 요청

3. **감사 로그와 규제 증빙**
   - 누가, 언제, 어떤 모델을, 어떤 데이터 등급으로, 어떤 정책 아래 썼는지 기록
   - 변경 불가능한 감사 로그, 승인 이력, 예외 처리 기록
   - 보안·준법·CISO 검토용 리포트 생성

4. **Agentic AI 통제**
   - tool call, MCP server call, RAG retrieval, API access 기록
   - agent가 접근할 수 있는 데이터와 외부로 보낼 수 있는 결과 통제
   - prompt injection, 과도한 tool 권한, cross-system data leakage 탐지

제품 정체성은 명확해야 한다. Gateway-first, governance-first, consulting-first는 서로 다른 사업이다.

현재 가장 좋은 포지션은 다음이다.

> **Veil AI는 gateway-first 제품이다. 거버넌스와 리포트는 관리 레이어이고, 컨설팅은 초기 진입 방식일 뿐 본질적인 BM이 아니다.**

## 초기 Wedge

Veil은 외부 또는 하이브리드 LLM 품질이 필요하면서도 민감정보가 반드시 섞이는 업무부터 시작해야 한다.

| 초기 Use Case | 왜 맞는가 | KPI |
| --- | --- | --- |
| 직원용 규정·상품 copilot | 내부 문서와 고객 맥락이 섞이고 강한 모델 품질이 필요 | 응답시간, 교육기간, 답변 일관성 |
| 여신·대출 문서 assistant | 신용정보와 기업 문서를 외부로 그대로 보낼 수 없음 | 심사 시간, turnaround time |
| 자산관리 advisor assistant | 고객 포트폴리오와 MNPI 리스크 존재 | follow-up time, advisor 생산성 |
| Agentic AI audit layer | 기존 DLP가 잘 커버하지 못하는 새 workflow | trace completeness, policy violation 탐지 |

가장 강한 wedge는 plain PII masking이 아니라 **agentic AI와 multi-model governance**일 가능성이 높다. 단순 마스킹은 이미 crowded market이다. 반면 agent workflow는 더 새롭고, 더 아프고, incumbent가 완전히 장악하지 못했다.

## 시장

시장을 “데이터 익명화 SaaS”로 정의하면 너무 작고 평범해 보인다.

더 좋은 정의는 다음이다.

> **국내 금융권 생성형 AI 프로젝트마다 붙는 필수 보안·거버넌스 control layer 예산**

공개 조달에서도 이 방향의 신호가 보인다.

| 기관 | 사업 | Veil 관련성 |
| --- | --- | --- |
| 한국수출입은행 | AI 시대 보안 패러다임 대응 정보보호 컨설팅 | 직접 fit |
| 한국투자공사 KIC | 내부 AI 플랫폼 및 인프라 구축 | 인접 |
| 금융결제원 | AIOps + LLM 시스템 | 인접 |
| 우리은행 | 생성형 AI 플랫폼 | 인접 |
| NH농협은행 | LG CNS와 생성형 AI 플랫폼 | 인접 |
| KB국민은행 | 생성형 AI 모델·GPU 인프라 | 인접 |
| IBK시스템 | 생성형 AI 시스템 구축 | 인접 |

초기 진입 순서는 다음이 현실적이다.

1. 정책금융기관
2. 공공 금융기관
3. 금융 인프라 기관
4. 대형 시중은행

이유는 단순하다. 공공·정책 금융기관은 조달이 공개되어 있고, 규제 압박이 강하며, 구조화된 PoC에 더 열려 있다.

## 경쟁

가장 큰 위험은 시장이 없다는 것이 아니다. 은행이 “이건 기존 벤더가 해주면 되는 것 아닌가?”라고 생각하는 것이다.

| 경쟁자 | 강점 | Veil의 리스크 |
| --- | --- | --- |
| Fasoo | 국내 DLP/DRM 강자, 은행 레퍼런스, AI-R DLP | 기존 계약에 모듈 추가로 팔 수 있음 |
| SI: LG CNS, 삼성SDS, SK C&C | 은행 납품 신뢰, 플랫폼 구축 주도권 | AI 플랫폼 안에 마스킹·로그 기능을 포함할 수 있음 |
| Elice 등 로컬 PII API | 한국어 PII 마스킹 역량 | 단순 마스킹 use case를 낮은 가격으로 가져갈 수 있음 |
| Microsoft/Azure 패턴 | enterprise trust, 내장 보안 기능 | 은행의 기존 cloud/SI 생태계에 포함됨 |
| Nightfall, Skyflow, Pangea, Protecto | 글로벌 AI/DLP tooling 성숙도 | 파트너를 통해 한국 시장 진입 가능 |

따라서 Veil은 “왜 은행이 직접 만들거나 기존 벤더에게 맡기면 안 되는가?”에 대한 답을 더 날카롭게 가져가야 한다.

가능한 답은 네 가지다.

1. **멀티벤더 중립성**
   - SI가 만든 통제 모듈은 특정 플랫폼에 묶인다.
   - Veil은 모델, 클라우드, 내부 시스템, SI stack을 가리지 않고 붙는다.

2. **규제 업데이트 속도**
   - 대형 suite는 호환성 테스트 때문에 업데이트가 느리다.
   - Veil은 AI 규제 변화에 맞춰 policy pack과 리포트 양식을 빠르게 배포한다.

3. **Agentic-native control**
   - 기존 DLP는 문서·파일 중심이다.
   - Veil은 prompt chain, RAG retrieval, tool call, MCP server, agent permission을 통제한다.

4. **벤치마크 투명성**
   - 모두가 “한국어 PII 잘 잡는다”고 말한다.
   - Veil은 한국 금융 AI 보안 벤치마크를 공개하고 수치로 경쟁해야 한다.

## 해자

기존의 “100% 탐지” 프레이밍은 위험하다. 완벽한 탐지를 믿을 구매자는 없고, 오히려 책임 리스크를 키운다. 더 좋은 표현은 다음이다.

> **Veil은 precision/recall tradeoff를 투명하게 보여주고, 은행이 설정 가능한 정책으로 리스크를 줄이며, 그 과정을 감사 증빙으로 남긴다.**

가능한 해자는 다음이다.

- **한국 금융 엔터티 커버리지:** 일반 PII가 아니라 신용, 여신, 담보, 계좌, 투자, 내부 은행 용어까지 포함한다.
- **벤치마크 소유:** 한국 금융 PII/신용정보/MNPI 탐지 벤치마크를 만들고 업계 기준점이 된다.
- **Policy pack 속도:** AI 기본법, 금융 AI 가이드라인, CISO 리포트, 기관별 규칙 변화에 빠르게 대응한다.
- **Cross-customer pattern learning:** 익명화된 공격 패턴, 오탐 케이스, 유출 시나리오가 고객 전체의 방어력을 높인다.
- **Agentic control depth:** MCP, RAG, tool-call, multi-agent audit을 incumbent보다 먼저 깊게 지원한다.

특히 벤치마크가 중요하다. 숫자가 없으면 “우리가 한국 금융 PII를 더 잘 잡는다”는 말은 주장에 그친다.

제안하는 벤치마크:

- Korean Financial AI Security Benchmark v1
- 200개 이상 민감 엔터티 카테고리
- 5만 개 이상 합성 및 법적으로 사용 가능한 문장·문서
- 도메인: 수신, 여신, 카드, 자산관리, 기업금융, 보험
- 지표: precision, recall, F1, latency, entity class별 false positive rate

## 비즈니스 모델

초기에는 self-serve SaaS보다 엔터프라이즈 보안 인프라에 가깝게 팔릴 가능성이 높다.

추천하는 진입 방식:

1. **Paid PoC / design partnership**
   - 좁은 업무, 실제 평가 데이터, 명확한 성공 지표

2. **구축 수수료**
   - gateway integration, policy mapping, SI/security integration

3. **연간 라이선스 + 유지보수**
   - 요청량, 사용자 수, 모델 수, 환경 수, compliance module 기준 과금

4. **Policy·benchmark subscription**
   - 규제 업데이트, 벤치마크 리포트, 엔터티 pack 업데이트

컨설팅은 첫 고객을 여는 데 도움이 될 수 있다. 하지만 회사의 본질이 컨설팅이 되면 안 된다. 초기 고객에게서 받은 요구사항도 최대한 재사용 가능한 product module로 바꿔야 한다.

## 리스크와 남은 질문

1. **Build vs. Buy**
   - 은행은 IT 자회사와 SI 파트너가 있다. Veil은 중립 gateway가 SI 내장 모듈보다 왜 나은지 증명해야 한다.

2. **Fasoo와 incumbent 관성**
   - Fasoo는 이미 은행 관계와 DLP 신뢰를 갖고 있다. Veil은 파트너 전략을 쓰거나, Fasoo가 약한 영역으로 비켜가야 한다.

3. **탐지 성능**
   - recall을 높이면 오탐이 늘고, precision을 높이면 민감정보를 놓칠 수 있다. 제품은 막연한 “고성능”이 아니라 설정 가능한 정책 모드를 가져야 한다.

4. **학습 데이터 역설**
   - 한국 금융 민감정보를 잘 잡으려면 한국 금융 데이터가 필요한데, 그 데이터는 규제 때문에 받기 어렵다. 합성 데이터, 고객사 내부 튜닝, secure evaluation, 규제 샌드박스 전략이 필요하다.

5. **운영 안정성**
   - 은행은 uptime, latency, incident response, logging integrity, support를 물을 것이다. 보안 gateway는 fragile prototype이면 안 된다.

6. **Scope creep**
   - gateway, governance SaaS, consulting은 서로 다른 사업이다. Veil은 하나의 primary identity를 정해야 한다.

## 정리된 전략 방향

아이디어를 가장 crisp하게 쓰면 다음과 같다.

> **Veil AI는 한국 금융기관이 frontier model과 agentic AI를 안전하게 도입할 수 있도록 돕는 model-neutral security gateway다. 민감정보를 마스킹하고, 모델 사용 정책을 집행하며, 모든 AI interaction을 기록하고, 컴플라이언스 증빙을 생성한다.**

버려야 할 것:

- “100% 탐지” 주장
- generic PII masking SaaS 포지션
- 넓은 컨설팅 회사처럼 보이는 문장
- 대시보드를 메인 제품처럼 말하는 방식
- LangSmith/Langfuse나 기존 DLP만으로도 가능한 기능을 핵심 차별점처럼 말하는 것

강조해야 할 것:

- 한국 금융 도메인 특화
- multi-model, model-neutral architecture
- agentic AI, MCP, RAG, tool-call governance
- 측정 가능한 벤치마크 성능
- 컴플라이언스 증빙과 빠른 policy update
- SI·보안 파트너와 함께 들어갈 수 있는 구조

## 다음에 더 발전시킬 질문

다음 버전에서는 아래 네 질문에 답해야 한다.

1. **Veil이 처음으로 보호할 정확한 workflow는 무엇인가?**
   - 예: 여신 문서 assistant, 직원용 AI copilot, agentic AI audit layer

2. **MVP는 무엇을 보여줘야 하는가?**
   - 현실적인 한국 금융 문서에서 masking + routing + audit log + policy block이 한 번에 동작하는 데모

3. **우월성을 어떤 숫자로 증명할 것인가?**
   - F1, recall, false positive rate, latency, trace completeness, compliance report 생성 시간

4. **은행이 왜 Fasoo나 SI에게 맡기면 안 되는가?**
   - 답은 구체적이어야 한다: model neutrality, agentic-native control, 한국 금융 벤치마크 성능, 규제 업데이트 속도 중 무엇이 진짜 차별점인지 골라야 한다.

## 유지할 주요 출처

- KB국민은행 AI 챗봇: https://omoney.kbstar.com/quics?articleClass=&articleId=139931&bbsMode=view&boardId=647&compId=b031438&page=C017648&searchCondition=title&searchStr=AI&viewPage=1
- NH농협 / Agentic AI Bank: https://www.ezyeconomy.com/news/articleView.html?idxno=229543
- 금융위 망분리 개선 로드맵: https://www.fsc.go.kr/no010101/83594
- 한국수출입은행 AI 보안 RFP: https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R25BK01163056&bidPbancOrd=000&fileSeq=4&fileType=&prcmBsneSeCd=03
- 금융결제원 AIOps + LLM RFP: https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R25BK00952122&bidPbancOrd=000&fileSeq=4&fileType=
- LG CNS / NH농협 생성형 AI 플랫폼: https://www.lgcns.com/kr/newsroom/press/detail.ko_0891
- KIC 내부 AI 플랫폼 조달: https://kic.kr/ko/news/announcements/bidding/vda6gv
- 개인정보보호법 제28조의2: https://www.law.go.kr/LSW//lsSideInfoP.do?docCls=jo&joBrNo=02&joNo=0028&lsiSeq=270351&urlMode=lsScJoRltInfoR
- 개인정보보호법 제28조의3: https://www.law.go.kr/LSW//lsSideInfoP.do?docCls=jo&joBrNo=03&joNo=0028&lsiSeq=270351&urlMode=lsScJoRltInfoR
- 신용정보법 제32조: https://www.law.go.kr/LSW//lsLawLinkInfo.do?chrClsCd=010202&lsId=001540&lsJoLnkSeq=1000722082&print=print
- AI 기본법: https://www.law.go.kr/lsInfoP.do?ancYnChk=0&lsId=014820
- Elice 한국어 PII 마스킹 API: https://elice.io/ko/resources/blog/pii-masking-api
- Fasoo AI-R DLP / DSPM reference: https://www.einpresswire.com/article/749862946/fasoo-dspm-wins-policy-management-solution-of-the-year-at-2025-cybersecurity-breakthrough-awards
