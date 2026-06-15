#!/usr/bin/env python3
import json
import mimetypes
import os
import posixpath
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from veil_gateway import (
    add_amount_masks,
    add_combination_risk,
    apply_rule_masking,
    mark_circuit_break,
    normalize_policy,
    public_gateway_result,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_INDEX = "index.html"
SCENARIOS = {"complaint", "loan", "devlog", "mnpi", "custom"}
STATIC_ALIASES = {
    "/veil_demo_v3.html": "/" + DEFAULT_INDEX,
}
SERVABLE_SUFFIXES = {
    ".html", ".htm", ".css", ".js", ".mjs", ".map",
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp",
    ".woff", ".woff2", ".ttf",
}


def log_debug(message):
    if env_bool("DEBUG", True):
        print("[veil-demo] {}".format(message), file=sys.stderr, flush=True)


def load_env(path):
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def bool_from_payload(value, default):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def config():
    api_key_configured = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    live_api_calls = env_bool("LIVE_API_CALLS", False)
    return {
        "api_key_configured": api_key_configured,
        "chat_model": os.environ.get("OPENAI_CHAT_MODEL", "gpt-5.4-mini"),
        "veil_model": os.environ.get("VEILAI_MODEL", "gpt-5.4-nano"),
        "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "live_api_calls": live_api_calls,
        "veilai_enabled": env_bool("VEILAI_ENABLED", True),
        "live_enabled": live_api_calls and api_key_configured,
    }


def request_config(payload):
    cfg = config()
    if "veilai_enabled" in payload:
        cfg["veilai_enabled"] = bool_from_payload(payload.get("veilai_enabled"), cfg["veilai_enabled"])
    elif "veil_ai_enabled" in payload:
        cfg["veilai_enabled"] = bool_from_payload(payload.get("veil_ai_enabled"), cfg["veilai_enabled"])
    return cfg


def normalize_scenario(value):
    scenario = str(value or "custom").strip().lower()
    return scenario if scenario in SCENARIOS else "custom"


def extract_output_text(payload):
    if isinstance(payload, dict):
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
        output = payload.get("output")
        if isinstance(output, list):
            pieces = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                for content in item.get("content", []):
                    if isinstance(content, dict):
                        text = content.get("text")
                        if isinstance(text, str):
                            pieces.append(text)
            if pieces:
                return "\n".join(pieces).strip()
    return json.dumps(payload, ensure_ascii=False)


def call_openai_response(model, prompt, cfg):
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    request = urllib.request.Request(
        "{}/responses".format(cfg["base_url"]),
        data=json.dumps({"model": model, "input": prompt}).encode("utf-8"),
        headers={
            "Authorization": "Bearer {}".format(api_key),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("OpenAI API error {}: {}".format(exc.code, detail)) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("OpenAI connection error: {}".format(exc.reason)) from exc

    return extract_output_text(json.loads(body))


PLAIN_CHAT_SYSTEM_PROMPT = (
    "당신은 한국어로 답하는 금융 업무 어시스턴트 챗봇입니다. "
    "사용자의 요청에 정확하고 간결하게, 자연스러운 한국어로 답하세요."
)

EXAMPLE_STYLE_SYSTEM_PROMPT = (
    "당신은 금융 업무 어시스턴트입니다. 아래에 사용자 요청과 참고 답변이 주어집니다. "
    "참고 답변과 같은 내용과 구조를 유지하되, 표현과 문장을 자연스럽게 바꿔 약간의 변화를 주어 "
    "한국어로 답변하세요. 참고 답변을 그대로 복사하지 마세요."
)


MASKING_ADVISOR_PROMPT = """당신은 외부 LLM 전송 전 '마스킹 자문 분석기'입니다. 입력 텍스트에서
(1) 개인 귀속 금액과 (2) 준식별자 조합(재식별 위험)을 찾아 JSON으로만 출력합니다.

[판단 기준]
1) sensitive_amounts — 특정 개인/계좌에 귀속된 금액(누군가의 잔액·잔고, 보유 자산, 개인이 실행한
   송금·이체액)만 포함. 맥락/일반 수치(이체 한도, 정책·상품 금액, 금리, 기업 매출·영업이익·부채 등
   재무 수치)는 절대 포함하지 않음.
2) 준식별자 조합 — 단독으로는 특정 못 하지만(나이/생년, 성별, 거주지, 직장·부서, 직책, 출신학교,
   전공, 학위·졸업연도, 보유자산, 가족구성 등) 여러 개가 합쳐지면 특정 개인을 지목할 수 있는 정보.
   '법인명 + 규모 + 대표 생년 + 직책'처럼 조합으로 특정 개인(예: 대표이사)을 지목하는 경우도 포함.
   reid_mask 에는 식별력이 가장 높은 표현 2~3개만(텍스트 그대로) 넣음.

입력에 그대로 등장하는 부분 문자열만 쓰고, 없는 값은 지어내지 않음.

[예시]
입력: "고객명: 황지호 / 이체 한도를 5,000만원으로 상향 / 현재 잔액 5,127만원"
출력: {"sensitive_amounts":["5,127만원"],"quasi_identifiers":[],"reid_count":0,"reidentifiable":false,"reid_mask":[]}
(잔액은 개인 귀속 → 마스킹, 한도 5,000만원은 맥락 → 보존)

입력: "대상기업: 정금속공업(주) / 종업원 18명 / 대표자: 1973년생 남성 / 대표이사 / 매출 47억, 운전자금 5억"
출력: {"sensitive_amounts":[],"quasi_identifiers":["정금속공업(주)","종업원 18명","1973년생","남성","대표이사"],"reid_count":5,"reidentifiable":true,"reid_mask":["정금속공업(주)","1973년생 남성 / 대표이사"]}
(법인+규모+생년+직책 조합으로 대표 1인 특정 가능 → 마스킹. 매출·운전자금 등 재무 수치는 보존)

입력: "결제 모듈 에러: password: P@ssw0rd!, rrn='731204 1773971', card=4000 0009 8524 0631"
출력: {"sensitive_amounts":[],"quasi_identifiers":[],"reid_count":0,"reidentifiable":false,"reid_mask":[]}
(비밀번호·주민번호·카드번호는 결정적 식별자로 규칙 엔진이 별도 차단 → 이 레이어는 관여하지 않음)

입력: "곧 발표될 A전자 미공개 실적으로 매수 전략 짜줘"
출력: {"sensitive_amounts":[],"quasi_identifiers":[],"reid_count":0,"reidentifiable":false,"reid_mask":[]}
(미공개 중요정보(MNPI)는 회로 차단으로 별도 처리 → 이 레이어는 관여하지 않음)

이제 아래 텍스트를 같은 형식의 JSON으로만 분석하세요."""


def combo_threshold():
    try:
        return max(2, int(os.environ.get("COMBO_MIN_IDENTIFIERS", "4")))
    except ValueError:
        return 4


def loose_json(text):
    if not text:
        return None
    body = text.strip()
    if body.startswith("```"):
        body = re.sub(r"^```(?:json)?", "", body).strip()
        body = re.sub(r"```$", "", body).strip()
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", body, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def detect_masking_advice(text, cfg):
    prompt = MASKING_ADVISOR_PROMPT + "\n\n[분석할 텍스트]\n" + text
    try:
        raw = call_openai_response(cfg["veil_model"], prompt, cfg)
    except Exception as exc:
        log_debug("masking advisor error: {}".format(exc))
        return None
    return loose_json(raw)


def run_llm_masking_layer(result, text, cfg):
    data = detect_masking_advice(text, cfg)
    if not isinstance(data, dict):
        return
    # Person-specific amounts only (the LLM excludes limits / financials / rates).
    amounts = [s for s in (data.get("sensitive_amounts") or []) if isinstance(s, str) and s.strip()]
    if amounts:
        add_amount_masks(result, amounts)
    # Quasi-identifier combination -> re-identification risk.
    quasi = data.get("quasi_identifiers") or []
    count = data.get("reid_count") if isinstance(data.get("reid_count"), int) else len(quasi)
    if data.get("reidentifiable") and count >= combo_threshold():
        spans = [s for s in (data.get("reid_mask") or []) if isinstance(s, str) and s.strip()]
        add_combination_risk(result, spans, count)


def gateway_preview(text, scenario, cfg=None):
    """Display-only analysis: what the gateway WOULD mask/block. The actual chat is
    always sent as plain text, so this never changes what the model receives."""
    result = apply_rule_masking(text, scenario)
    if scenario == "mnpi":
        mark_circuit_break(
            result,
            "미공개 중요정보 (MNPI)",
            "미공개 중요정보",
            "자본시장법 §174 (미공개중요정보 이용금지)",
            reason="미공개 중요정보 이용 정황으로 외부 모델 전송을 차단",
        )
        return result
    # Quasi-identifier combination is open-vocabulary, so a small LLM layer counts
    # them on free-typed input and masks the most identifying few in the preview.
    if cfg and cfg.get("live_enabled") and cfg.get("veilai_enabled") and scenario == "custom":
        run_llm_masking_layer(result, text, cfg)
    return result


def latest_user_message(messages):
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def build_plain_chat_prompt(messages):
    lines = [PLAIN_CHAT_SYSTEM_PROMPT, "", "Conversation:"]
    for message in messages[-12:]:
        role = message.get("role", "user")
        content = str(message.get("content", ""))
        lines.append("{}: {}".format(role, content))
    return "\n".join(lines)


def build_example_prompt(user_text, reference):
    return "\n".join([
        EXAMPLE_STYLE_SYSTEM_PROMPT,
        "",
        "[사용자 요청]",
        user_text,
        "",
        "[참고 답변]",
        reference,
        "",
        "위 참고 답변을 바탕으로 같은 의미를 유지하되 표현을 바꿔 한국어로 답변하세요.",
    ])


def default_block_reply(gateway_result):
    blocked = [item["item"] for item in gateway_result["findings"] if item["action"] == "BLOCK"]
    return (
        "VeilAI가 이 요청을 차단했습니다. 차단 사유: {}. "
        "회로 차단(circuit break)으로 외부 모델에 전송하지 않았습니다."
    ).format(", ".join(blocked) or "정책 위반")


def handle_chat(payload):
    cfg = request_config(payload)
    messages = payload.get("messages", [])
    scenario = normalize_scenario(payload.get("scenario", "custom"))
    reference = str(payload.get("reference", "") or "").strip()
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a non-empty array")

    recent_messages = messages[-12:]
    latest_user = latest_user_message(recent_messages)
    if not latest_user.strip():
        raise ValueError("latest user message is empty")

    # Display-only preview of what the gateway WOULD mask/block. The deck shows this;
    # the actual chat below is always sent as plain text (no masking, no restore).
    gateway_result = gateway_preview(latest_user, scenario, cfg)
    policy = normalize_policy(gateway_result["policy"])
    # MNPI is the only circuit break, and only while the VeilAI gateway is on.
    circuit_break = scenario == "mnpi" and cfg["veilai_enabled"]

    called_external = False
    if circuit_break:
        assistant = reference or default_block_reply(gateway_result)
        model = "circuit-break"
    elif cfg["live_enabled"]:
        # The MNPI reference is a refusal message, so only imitate references for the
        # normal examples; the MNPI-off case and free chat go as plain conversation.
        if reference and scenario != "mnpi":
            prompt = build_example_prompt(latest_user, reference)
        else:
            prompt = build_plain_chat_prompt(recent_messages)
        assistant = call_openai_response(cfg["chat_model"], prompt, cfg)
        called_external = True
        model = cfg["chat_model"]
    else:
        assistant = (
            reference
            if reference and scenario != "mnpi"
            else "(데모: 외부 모델이 비활성화되어 응답을 생성할 수 없습니다.)"
        )
        model = "offline"

    return {
        **public_gateway_result(gateway_result),
        "assistant": assistant,
        "policy": policy,
        "circuit_break": circuit_break,
        "model": model,
        "called_external_model": called_external,
    }


def handle_analyze(payload):
    scenario = normalize_scenario(payload.get("scenario", "custom"))
    text = str(payload.get("text", ""))
    if not text.strip():
        raise ValueError("text must be non-empty")
    gateway_result = gateway_preview(text, scenario)
    return {
        **public_gateway_result(gateway_result),
        "policy": normalize_policy(gateway_result["policy"]),
        "circuit_break": gateway_result["policy"] == "BLOCK",
        "called_external_model": False,
    }


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "VeilAIGateway/0.3"

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/config"):
            self.send_json(config())
            return
        self.serve_static()

    def do_POST(self):
        try:
            if self.path.startswith("/api/chat"):
                response = handle_chat(self.read_json())
                log_debug(
                    "chat scenario={} policy={} external={} findings={}".format(
                        response.get("scenario"),
                        response.get("policy"),
                        response.get("called_external_model"),
                        len(response.get("findings", [])),
                    )
                )
                self.send_json(response)
                return
            if self.path.startswith("/api/analyze"):
                response = handle_analyze(self.read_json())
                log_debug(
                    "analyze scenario={} policy={} findings={}".format(
                        response.get("scenario"),
                        response.get("policy"),
                        len(response.get("findings", [])),
                    )
                )
                self.send_json(response)
                return
            self.send_error(404, "Not found")
        except ValueError as exc:
            log_debug("bad request path={} error={}".format(self.path, exc))
            self.send_json({"error": str(exc)}, status=400)
        except Exception as exc:
            log_debug("handler error path={} error={}".format(self.path, exc))
            self.send_json({"error": str(exc)}, status=502)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_static(self):
        parsed = urllib.parse.urlparse(self.path)
        request_path = urllib.parse.unquote(parsed.path)
        if request_path == "/":
            request_path = "/" + DEFAULT_INDEX
        request_path = STATIC_ALIASES.get(request_path, request_path)
        clean_path = posixpath.normpath(request_path).lstrip("/")
        file_path = (ROOT / clean_path).resolve()
        try:
            file_path.relative_to(ROOT)
        except ValueError:
            self.send_error(403, "Forbidden")
            return
        if not file_path.is_file():
            self.send_error(404, "Not found")
            return
        if file_path.name.startswith(".") or file_path.suffix.lower() not in SERVABLE_SUFFIXES:
            # Never serve dotfiles (.env) or backend source (.py/.md) over HTTP.
            self.send_error(404, "Not found")
            return
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(file_path))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    load_env(ROOT / ".env")
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8088"))
    server = ThreadingHTTPServer((host, port), DemoHandler)
    cfg = config()
    print("Veil AI gateway running at http://{}:{}/{}".format(host, port, DEFAULT_INDEX))
    print(
        "LIVE_API_CALLS={} VEILAI_ENABLED={} COMBO_MIN_IDENTIFIERS={}".format(
            cfg["live_api_calls"], cfg["veilai_enabled"], combo_threshold()
        )
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()


if __name__ == "__main__":
    try:
        main()
    except OSError as exc:
        print("Failed to start server: {}".format(exc), file=sys.stderr)
        sys.exit(1)
