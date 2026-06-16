import re
from copy import deepcopy


ACTION_RANK = {
    "PASS": 0,
    "MASK": 1,
    "TOKENIZE": 1,
    "PSEUDONYMIZE": 1,
    "REVIEW": 2,
    "BLOCK": 3,
}

PUBLIC_POLICIES = {"PASS", "MASK", "REVIEW", "BLOCK"}
MASK_ACTIONS = {"MASK", "TOKENIZE", "PSEUDONYMIZE"}

PHONE_RE = re.compile(r"\b01[016789]-?\d{3,4}-?\d{4}\b")
RRN_RE = re.compile(r"\b\d{6}[- ]?\d{7}\b")
HANGUL_RRN_RE = re.compile(r"[영공일이삼사오육칠팔구]{6}\s*\d{7}")
ACCOUNT_RE = re.compile(r"\b\d{2,4}-\d{2,6}-\d{5,10}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
SECRET_RE = re.compile(
    r"(?im)\b(password|passwd|secret|api[_-]?key|token|private[_-]?key)\s*[:=]\s*([^\s]+)"
)
INTERNAL_HOST_RE = re.compile(r"\b[a-z0-9][a-z0-9.-]*\.internal(?:\.[a-z0-9.-]+)?\b", re.I)
SK_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b")
BALANCE_RE = re.compile(r"(잔액\s*)[0-9,]+만원")
CREDIT_RE = re.compile(r"(신용등급\s*)[0-9]+등급")
DELINQUENCY_RE = re.compile(r"연체\s*[0-9]+건")
KOREAN_SURNAMES = (
    "김이박최정강조윤장임한오서신권황안송전홍유고문양손배백허남심노하곽성차주우구"
    "민류진지엄채원천방공현함변염여추도소석선설마길연위표명기반왕금옥육인맹제모탁국편"
)
NAME_CONTEXT_RE = re.compile(
    r"(?<![가-힣])([" + KOREAN_SURNAMES + r"][가-힣]{1,2})"
    r"(?=(?:가|이|은|는|을|를|씨|님|께서|에게|한테|와|과|도|만)(?![가-힣]))"
)
# Common nouns / entity words that match the surname pattern but are not people.
NAME_STOPWORDS = {
    "고객", "직원", "대표", "잔액", "한도", "계좌", "신용", "카드", "등급", "금액",
    "이체", "송금", "은행", "기업", "회사", "본사", "심사", "여신", "담보", "매출",
    "부채", "운전", "주민", "당사", "귀사", "민원", "신한", "국민", "우리", "하나",
    "농협", "토스", "카카오", "업종", "연체", "연매출", "연봉", "연락", "연간",
    "연결", "신청", "신규", "신탁", "제품", "제출", "기관", "기준", "영업", "잔고",
}
NAME_FIELD_RE = re.compile(
    r"(?P<label>고객명|성명|이름|name)(?P<sep>\s*[:=]\s*)(?P<name>[가-힣]{2,4}|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})",
    re.I,
)
AMBIGUOUS_RE = re.compile(
    r"(애매|모호|확실하지|잘 모르|추정|infer|guess|maybe|probably|looks like|"
    r"비슷한|대충|일부만|부분만|복원|reconstruct|재식별|역추적)",
    re.I,
)
RECONSTRUCT_RE = re.compile(r"(원문|실명|주민번호|계좌번호|카드번호|비밀번호).{0,20}(복원|추정|알려|찾아|reconstruct)", re.I)

KNOWN_NAMES = ("황지호", "김민준", "이서연", "박지훈", "최유진")
HANGUL_DIGITS = {
    "영": "0",
    "공": "0",
    "일": "1",
    "이": "2",
    "삼": "3",
    "사": "4",
    "오": "5",
    "육": "6",
    "칠": "7",
    "팔": "8",
    "구": "9",
}


def policy_from_rank(rank):
    if rank >= ACTION_RANK["BLOCK"]:
        return "BLOCK"
    if rank >= ACTION_RANK["REVIEW"]:
        return "REVIEW"
    if rank >= ACTION_RANK["MASK"]:
        return "MASK"
    return "PASS"


def highest_policy(findings):
    rank = 0
    for finding in findings:
        rank = max(rank, ACTION_RANK.get(finding.get("action", "PASS"), 0))
    return policy_from_rank(rank)


def normalize_action(action):
    action = str(action or "PASS").upper()
    return action if action in ACTION_RANK else "REVIEW"


def normalize_policy(policy):
    policy = str(policy or "PASS").upper()
    if policy in PUBLIC_POLICIES:
        return policy
    return policy_from_rank(ACTION_RANK.get(policy, 0))


def finding(item, category, basis, action, engine="rule", reason=""):
    return {
        "item": str(item),
        "category": str(category),
        "basis": str(basis),
        "action": normalize_action(action),
        "engine": engine,
        "reason": reason,
    }


class TokenVault:
    def __init__(self):
        self.counts = {}
        self.restore_values = {}
        self.public_map = []
        self.existing_by_value = {}

    def token(self, label, original, action="PSEUDONYMIZE", restore=True):
        original = str(original)
        cache_key = (label, original, action, restore)
        if cache_key in self.existing_by_value:
            return self.existing_by_value[cache_key]
        self.counts[label] = self.counts.get(label, 0) + 1
        token = "⟦{}_{:03d}⟧".format(label, self.counts[label])
        self.existing_by_value[cache_key] = token
        if restore:
            self.restore_values[token] = original
        self.public_map.append(
            {
                "token": token,
                "label": label,
                "action": action,
                "reversible": bool(restore),
            }
        )
        return token

    def alias(self, original, prefix="고객", action="PSEUDONYMIZE", restore=True):
        """가명화(pseudonymize)용 — 사람처럼 읽히는 가명(고객A, 고객B …)을 만든다.
        토큰화(불투명 ⟦토큰⟧)와 달리, 치환 후에도 문장이 자연스럽게 읽히도록."""
        original = str(original)
        cache_key = ("ALIAS", original, action, restore)
        if cache_key in self.existing_by_value:
            return self.existing_by_value[cache_key]
        self.counts["ALIAS"] = self.counts.get("ALIAS", 0) + 1
        token = "{}{}".format(prefix, chr(ord("A") + (self.counts["ALIAS"] - 1) % 26))
        self.existing_by_value[cache_key] = token
        if restore:
            self.restore_values[token] = original
        self.public_map.append({"token": token, "label": "P", "action": action, "reversible": bool(restore)})
        return token


def luhn_ok(value):
    digits = [int(ch) for ch in re.sub(r"\D", "", value)]
    if len(digits) < 13:
        return False
    total = 0
    parity = len(digits) % 2
    for idx, digit in enumerate(digits):
        if idx % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def hangul_digits_to_number(value):
    return "".join(HANGUL_DIGITS.get(ch, ch) for ch in value.replace(" ", ""))


def add_finding(findings, seen, new_finding):
    key = (
        new_finding.get("item"),
        new_finding.get("category"),
        new_finding.get("action"),
        new_finding.get("engine"),
    )
    if key in seen:
        return
    seen.add(key)
    findings.append(new_finding)


def apply_rule_masking(text, scenario="complaint"):
    raw = text or ""
    sanitized = raw
    findings = []
    seen = set()
    vault = TokenVault()

    for match in SK_KEY_RE.findall(sanitized):
        add_finding(findings, seen, finding("OpenAI/API key", "접근매체", "내부 시크릿 정책", "BLOCK",
                                            reason="운영 자격증명 — 외부 전송 차단, 즉시 교체 권장"))
    sanitized = SK_KEY_RE.sub("〔차단:SECRET〕", sanitized)

    def replace_secret(match):
        key = match.group(1)
        add_finding(findings, seen, finding(key, "접근매체", "전자금융거래법 §2", "BLOCK",
                                            reason="운영 자격증명 — 외부 전송 차단, 즉시 교체 권장"))
        return "{}: 〔차단:SECRET〕".format(key)

    sanitized = SECRET_RE.sub(replace_secret, sanitized)

    # 주민번호는 고유식별자지만, 업무(디버깅 등)는 이어갈 수 있도록 차단이 아닌 가명화로 처리.
    def replace_hangul_rrn(match):
        normalized = hangul_digits_to_number(match.group(0))
        item = "주민번호 변형 {}".format(normalized[:6] + "-*******")
        add_finding(findings, seen, finding(item, "고유식별정보", "개인정보보호법 시행령 §19", "TOKENIZE"))
        return vault.token("RRN", match.group(0), action="TOKENIZE")

    sanitized = HANGUL_RRN_RE.sub(replace_hangul_rrn, sanitized)

    def replace_rrn(match):
        add_finding(findings, seen, finding("주민번호", "고유식별정보", "개인정보보호법 시행령 §19", "TOKENIZE"))
        return vault.token("RRN", match.group(0), action="TOKENIZE")

    sanitized = RRN_RE.sub(replace_rrn, sanitized)

    def replace_phone(match):
        value = match.group(0)
        add_finding(findings, seen, finding(value, "식별정보", "신용정보법 §2-1의2", "TOKENIZE"))
        return vault.token("PHONE", value, action="TOKENIZE")

    sanitized = PHONE_RE.sub(replace_phone, sanitized)

    def replace_account(match):
        value = match.group(0)
        add_finding(findings, seen, finding(value, "거래내용정보", "신용정보법 §2-1의3", "TOKENIZE"))
        return vault.token("ACCT", value, action="TOKENIZE")

    sanitized = ACCOUNT_RE.sub(replace_account, sanitized)

    def replace_card(match):
        value = match.group(0).strip()
        digits = re.sub(r"\D", "", value)
        if not luhn_ok(value):
            return value
        add_finding(
            findings,
            seen,
            finding("카드 {}".format(digits[:4] + "…" + digits[-4:]), "거래내용정보", "신용정보법 §2-1의3", "TOKENIZE"),
        )
        return vault.token("CARD", value, action="TOKENIZE")

    sanitized = CARD_RE.sub(replace_card, sanitized)

    def replace_name_field(match):
        label = match.group("label")
        sep = match.group("sep")
        name = match.group("name")
        add_finding(findings, seen, finding(name, "식별정보", "신용정보법 §2-1의2", "PSEUDONYMIZE"))
        return "{}{}{}".format(label, sep, vault.alias(name))

    sanitized = NAME_FIELD_RE.sub(replace_name_field, sanitized)

    for name in KNOWN_NAMES:
        if name in sanitized:
            add_finding(findings, seen, finding(name, "식별정보", "신용정보법 §2-1의2", "PSEUDONYMIZE"))
            sanitized = sanitized.replace(name, vault.alias(name))

    def replace_context_name(match):
        name = match.group(1)
        if name in NAME_STOPWORDS:
            return name
        add_finding(findings, seen, finding(name, "식별정보", "신용정보법 §2-1의2", "PSEUDONYMIZE"))
        return vault.alias(name)

    sanitized = NAME_CONTEXT_RE.sub(replace_context_name, sanitized)

    def replace_balance(match):
        value = match.group(0)
        add_finding(findings, seen, finding("잔액", "거래내용정보 (맥락)", "신용정보법 §2-1의3", "TOKENIZE"))
        return vault.token("AMOUNT_TXN", value, action="TOKENIZE")

    sanitized = BALANCE_RE.sub(replace_balance, sanitized)

    def replace_credit(match):
        value = match.group(0)
        add_finding(findings, seen, finding("신용등급", "기타 신용판단정보", "신용정보법 §2-1의6", "TOKENIZE"))
        return vault.token("CREDIT_GRADE", value, action="TOKENIZE")

    sanitized = CREDIT_RE.sub(replace_credit, sanitized)

    def replace_delinquency(match):
        value = match.group(0)
        add_finding(findings, seen, finding("연체 이력", "신용도판단정보", "신용정보법 §2-1의4", "TOKENIZE"))
        return vault.token("DELINQ", value, action="TOKENIZE")

    sanitized = DELINQUENCY_RE.sub(replace_delinquency, sanitized)

    # 법인+생년+직책 '결합 재식별'은 정규식으로 표현 불가능한 의미 판단이라, 룰 레이어가
    # 아니라 L2 VeilAI 판단(add_combination_risk)에서 처리한다. (gateway_preview 참고)

    for match in INTERNAL_HOST_RE.findall(sanitized):
        add_finding(findings, seen, finding(match, "기술자산 (대외비)", "내부 등급분류", "REVIEW"))
    sanitized = INTERNAL_HOST_RE.sub("⟨검토:internal-host⟩", sanitized)

    if RECONSTRUCT_RE.search(raw):
        add_finding(findings, seen, finding("보호값 복원 요청", "정책 위반", "VeilAI restore policy", "BLOCK"))
    elif should_flag_uncertain(raw, sanitized, findings):
        add_finding(findings, seen, finding("불확실한 민감정보 판단", "회색지대", "VeilAI confidence policy", "REVIEW"))

    if not findings:
        add_finding(findings, seen, finding("탐지 없음", "비민감", "—", "PASS"))

    result = {
        "raw": raw,
        "scenario": scenario,
        "sanitized": sanitized,
        "findings": findings,
        "policy": highest_policy(findings),
        "restore_map": vault.public_map,
        "_restore_values": vault.restore_values,
        "steps": [],
    }
    result["steps"] = build_steps(result, llm_used=False)
    return result


def should_flag_uncertain(original, sanitized, findings):
    if not original.strip():
        return False
    if any(item.get("action") == "BLOCK" for item in findings):
        return False
    has_soft_signal = any(item.get("action") in MASK_ACTIONS for item in findings)
    has_contextual_signal = any(
        marker in original
        for marker in ("고객", "대표", "계좌", "신용", "잔액", "카드", "rrn", "주민", "내부", "로그", "직원")
    )
    return bool(AMBIGUOUS_RE.search(original) and (has_soft_signal or has_contextual_signal or sanitized != original))


def build_steps(result, llm_used=False):
    findings = [item for item in result.get("findings", []) if item.get("item") != "탐지 없음"]
    rule_items = [item for item in findings if item.get("engine") == "rule"]
    llm_items = [item for item in findings if item.get("engine") == "llm"]
    restore_count = len(result.get("restore_map", []))
    blocked = [item for item in findings if item.get("action") == "BLOCK"]
    review = [item for item in findings if item.get("action") == "REVIEW"]

    steps = [
        {
            "layer": "L1",
            "title": "Rule-based masking",
            "engine": "rule",
            "found": summarize_findings(rule_items) or ["No deterministic sensitive pattern detected"],
            "note": "Regex, checksum, Korean normalization, context keywords, and reversible token vault.",
        },
        {
            "layer": "L2",
            "title": "VeilAI gray-zone judgment",
            "engine": "ai",
            "found": summarize_findings(llm_items)
            or ([result.get("veil_assessment", {}).get("summary", "Model assessment complete")] if llm_used else ["AI layer not called for this request"]),
            "note": "LLM only sees sanitized text plus rule findings; it flags gray-zone risk and uncertainty.",
        },
        {
            "layer": "B",
            "title": "Token vault",
            "engine": "rule",
            "found": ["{} reversible token(s) available for internal response restoration".format(restore_count)],
            "note": "BLOCK placeholders are intentionally irreversible.",
        },
        {
            "layer": "GATE",
            "title": "Policy gate",
            "engine": "rule+ai",
            "found": ["Policy: {}".format(result.get("policy", "PASS"))],
            "note": "BLOCK/REVIEW are not sent to the external chat model; MASK/PASS use sanitized input.",
        },
        {
            "layer": "B2",
            "title": "Restore",
            "engine": "rule",
            "found": ["Restore eligible response tokens after external model output"] if restore_count else ["No restoration needed"],
            "note": "Restoration happens only inside the trusted app response path.",
        },
    ]
    if blocked:
        steps[3]["found"].append("Blocked: " + ", ".join(item["item"] for item in blocked[:4]))
    if review:
        steps[3]["found"].append("Review: " + ", ".join(item["item"] for item in review[:4]))
    return steps


def summarize_findings(findings):
    summary = []
    for item in findings[:6]:
        summary.append("{} → {}".format(item.get("item"), item.get("action")))
    if len(findings) > 6:
        summary.append("+{} more".format(len(findings) - 6))
    return summary


def public_gateway_result(result):
    public = deepcopy(result)
    public.pop("_restore_values", None)
    return public


def mark_circuit_break(result, item, category, basis, reason="", engine="llm"):
    """Force a BLOCK (circuit break) on a preview result, e.g. the MNPI demo case.
    Defaults to engine='llm' so semantic blocks (MNPI) surface under the L2 VeilAI
    judgment layer, not L1 regex masking."""
    result["findings"] = [f for f in result.get("findings", []) if f.get("item") != "탐지 없음"]
    result["findings"].append(finding(item, category, basis, "BLOCK", engine=engine, reason=reason))
    result["policy"] = "BLOCK"
    result["steps"] = build_steps(result, llm_used=engine == "llm")
    return result


def mark_review(result, item, category, basis, reason="", engine="llm"):
    """Force a REVIEW (human-in-the-loop) verdict, e.g. the sensitive-data consent case.
    Defaults to engine='llm' so it surfaces under the L2 VeilAI judgment layer — this is
    a semantic call the rule layer cannot make, not a deterministic pattern match."""
    result["findings"] = [f for f in result.get("findings", []) if f.get("item") != "탐지 없음"]
    result["findings"].append(finding(item, category, basis, "REVIEW", engine=engine, reason=reason))
    result["policy"] = "REVIEW"
    result["steps"] = build_steps(result, llm_used=engine == "llm")
    return result


def add_combination_risk(result, spans, count):
    """Re-identification risk: too many quasi-identifiers combined. Masks only the
    most identifying few (display-only MASK, not a circuit break)."""
    result["findings"] = [f for f in result.get("findings", []) if f.get("item") != "탐지 없음"]
    masked = []
    for span in spans:
        span = str(span).strip()
        if span and span in result["sanitized"]:
            token = "⟦COMBO_{:03d}⟧".format(len(masked) + 1)
            result["sanitized"] = result["sanitized"].replace(span, token)
            result.setdefault("restore_map", []).append(
                {"token": token, "label": "COMBO", "action": "TOKENIZE", "reversible": False}
            )
            masked.append(span)
    result["findings"].append(
        finding(
            "결합 식별 위험 (준식별자 {}개)".format(count),
            "결합식별 (재식별 위험)",
            "개인정보보호법 §2 (가명·익명처리)",
            "TOKENIZE",
            engine="llm",
            reason="단독으로는 비민감하나 조합 시 특정 가능 — 식별력 높은 {}개 마스킹".format(len(masked)),
        )
    )
    result["policy"] = highest_policy(result["findings"])
    result["steps"] = build_steps(result, llm_used=True)
    return masked


def add_amount_masks(result, spans):
    """Mask only LLM-confirmed person-specific amounts; context amounts (limits,
    financials, rates) are left untouched. Display-only."""
    result["findings"] = [f for f in result.get("findings", []) if f.get("item") != "탐지 없음"]
    masked = []
    for span in spans:
        span = str(span).strip()
        if span and span in result["sanitized"]:
            token = "⟦AMOUNT_{:03d}⟧".format(len(masked) + 1)
            result["sanitized"] = result["sanitized"].replace(span, token)
            result.setdefault("restore_map", []).append(
                {"token": token, "label": "AMOUNT", "action": "TOKENIZE", "reversible": False}
            )
            masked.append(span)
    if masked:
        result["findings"].append(
            finding(
                "개인 귀속 금액",
                "거래내용정보 (개인 귀속)",
                "신용정보법 §2-1의3",
                "TOKENIZE",
                engine="llm",
                reason="개인·계좌 특정 금액 {}건만 마스킹 (한도·재무 등 맥락 수치는 보존)".format(len(masked)),
            )
        )
        result["policy"] = highest_policy(result["findings"])
        result["steps"] = build_steps(result, llm_used=True)
    return masked
