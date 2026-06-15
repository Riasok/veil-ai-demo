# Veil AI Demo Agent Log

Last revised: 2026-06-14

## Purpose

This project is a runnable demo for an agentic financial LLM gateway. The demo shows a chat interface backed by a gateway layer that masks, tokenizes, blocks, reviews, and restores sensitive Korean financial/customer data before an external chat model is allowed to see it.

The intended product story is:

- A user chats normally in `Agentic Chatbot for Agentic Chat Gateway`.
- The gateway checks the user message before model use.
- Rule-based masking catches deterministic sensitive data.
- VeilAI catches gray-zone risks that rules alone may miss.
- The external LLM receives only sanitized text when policy allows.
- The trusted app can restore reversible tokens on the response path.
- If the request is uncertain or unsafe, the gateway flags `REVIEW` or `BLOCK`.

## Main Files

- `index.html`: single-page UI for chat, examples, and the lower gateway processing deck.
- `server.py`: Python stdlib HTTP server and API layer.
- `veil_gateway.py`: masking, policy, prompt, merge, restore, and pipeline logic.
- `.env`: local runtime configuration, with the API key intentionally blank.
- `.env.example`: same shape as `.env` for reference.
- `docs/demo_plan.md`: original Korean demo/product plan.
- `docs/business_brief.md`: broader business/product notes.
- `archive/legacy_demo.html`: backup/reference HTML from an earlier version.
- `agent.md`: this implementation log.

## Runtime

Run:

```bash
python3 server.py
```

Current local URL:

```text
http://127.0.0.1:8088/
```

Important `.env` keys:

```text
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-5.4-mini
VEILAI_MODEL=gpt-5.4-nano
OPENAI_BASE_URL=https://api.openai.com/v1
LIVE_API_CALLS=false
VEILAI_ENABLED=true
RESTORE_RESPONSES=true
BLOCK_ON_REVIEW=true
DEBUG=true
HOST=127.0.0.1
PORT=8088
```

`LIVE_API_CALLS=false` means the app uses the real gateway logic but local fallback responses instead of calling the external OpenAI API. When `OPENAI_API_KEY` is filled and `LIVE_API_CALLS=true`, `server.py` can call the configured models.

## Current UX Contract

Examples:

- The four examples live in a compact strip inside the main chat panel.
- Clicking an example only fills the chat input.
- Clicking an example must not pre-run analysis.
- No example is selected by default.
- `Clear` removes any selected example state as well as clearing the chat/input.
- Free-typed chats without a selected example are sent as `scenario: "custom"`.
- The lower `입력 · 출력 / 처리 로직` deck is hidden before send.
- After an actual `/api/chat` request with VeilAI ON, the lower deck opens using that request's gateway result.
- `/api/chat` returns gateway deck data, and the lower deck displays the active result.

Chat:

- The composer stays fixed at the bottom of the chat panel.
- The chat log scrolls internally.
- There is no visible right-side trace rail in the current UI.
- `Clear` clears the input, chat messages, selected example, trace, and lower deck state.
- Chat bubbles render message text plainly without inline highlighting.

VeilAI toggle:

- `VeilAI ON`: sends messages through the gateway path.
- `VeilAI OFF`: sends plain chat without visible trace/deck UI.
- If a chat is sent while OFF, stale gateway analysis is cleared and does not reappear when toggled ON later.

Trace:

- The trace rail was removed from the visible UI.
- Right-rail trace DOM and JavaScript were removed from `index.html`.
- The lower deck is now the only visible gateway trace surface.

## Non-Negotiable UI Invariants

Keep these intact unless the product direction changes:

- Examples are input fillers only.
- The gateway/deck must not run before `전송`.
- The lower deck must stay hidden before send and while VeilAI is OFF.
- If the lower deck is re-enabled, it must use `/api/chat` results, not `/api/analyze` results.
- The chat composer must not move downward because of examples or future trace content.
- Chat message text should render plainly, without masking/highlight colors.
- If `처리 로직` is re-enabled, it must remain visible and populated after a chat response.
- Do not animate the `.front` or `.back` flip faces directly, because they need stable 3D transforms.
- `VeilAI OFF` means plain chat only: no trace panel, no lower deck, no stale analysis.
- Turning VeilAI back on should not resurrect analysis from an OFF-mode chat.

## Current Layout Fixes

The right trace used to stretch the whole chat grid and push the composer down. The current UI removes the right rail entirely. The remaining chat layout fix is:

- `.chat-grid` is single-column with a fixed working height: `height: clamp(560px, 68vh, 700px)`.
- `.chat-main` is a fixed-height flex column.
- `.chat-log` scrolls internally with `min-height: 0`.
- `.chat-compose` is `flex: none`.
- Examples sit above the chat log and do not move the composer.

This keeps the chat bar in the same place.

## API Flow

`GET /api/config`

- Returns runtime mode and model config.
- Used by the frontend to initialize `veilai_enabled`.

`POST /api/chat`

- Main interactive path.
- Receives current conversation messages and `veilai_enabled`.
- Runs gateway on the latest user message.
- If policy allows and live mode is configured, calls the external chat model.
- Otherwise returns a local fallback response.
- Returns gateway fields retained for internal/debug use:
  - `raw`
  - `sanitized`
  - `findings`
  - `policy`
  - `restore_map`
  - `steps`
  - `assistant`
  - `assistant_sanitized`
  - `restored`
  - `called_external_model`
  - `veil_ai_io`
  - `external_llm_input`

`POST /api/analyze`

- Still exists for debugging/direct analysis.
- The current UI no longer calls it.
- This prevents the demo from looking like analysis was done before the user actually chatted.

`GET /api/veil-schema`

- Documents the VeilAI prompt/input/output contract for inspection.

## Gateway Logic

Core entry point:

```text
run_gateway(text, scenario, cfg)
```

Rule layer:

```text
apply_rule_masking(text, scenario)
```

This produces:

- sanitized text
- findings
- policy
- restore map
- private restore values

VeilAI layer:

```text
build_veil_masking_input(rule_result, scenario)
parse_veil_json(raw_veil)
merge_veil_assessment(rule_result, veil_assessment)
```

The VeilAI layer receives already sanitized text plus rule findings. It should not reconstruct original values. If uncertain, it should choose `REVIEW`.

Restore path:

```text
restore_text(assistant_sanitized, restore_values)
```

Only reversible tokens from `MASK`, `TOKENIZE`, or `PSEUDONYMIZE` are eligible for trusted response restoration. `BLOCK` placeholders are intentionally irreversible.

## Rule-Based Coverage

Implemented rule coverage includes:

- Korean phone numbers.
- Resident registration numbers, including numeric and Korean-digit variants.
- Account-like numbers using banking context.
- Card numbers with Luhn validation.
- Secrets, passwords, API keys, private keys, and internal credentials.
- Explicit customer names from labels and known demo names.
- Balance/amount context.
- Credit grade context.
- Delinquency context.
- Corporate + birth year + role combination identification.
- Internal hosts/domains and technical assets.
- Prompt attempts to reconstruct, decode, reveal, or recover protected values.
- Unknown or hard-to-classify sensitive context is flagged as `REVIEW` when appropriate.

## Scenario Examples

Current example strip:

- `민원 응대`: free-form complaint response with customer name, phone, account, balance, delinquency, and credit grade.
- `여신 심사`: corporate loan memo with company, employee count, birth year, and representative role.
- `고객 리스트 분석`: CSV-style customer list with names, phones, accounts, balances, credit grades, and delinquency.
- `개발 디버깅`: logs/code with RRN-like values, card data, password, and internal host.

Important behavior:

- Examples are sample inputs only.
- They do not trigger gateway processing until `전송`.
- Examples are the only visible demo controls besides chat and the VeilAI toggle.

## Model Behavior

Configured model names:

- Chat model: `gpt-5.4-mini`
- VeilAI model: `gpt-5.4-nano`

These are read from `.env`. The frontend does not display `gpt-5.4-nano`, `local gateway`, `LOCAL`, or `PASS · LOCAL`, because those labels confused the demo narrative.

When live mode is off:

- The gateway still masks and produces trace/steps.
- The assistant response comes from `local_reply()`.
- `local_reply()` has neutral `custom` wording so free chats do not look like one of the canned examples.
- `called_external_model=false`.

When live mode is on and an API key is present:

- `run_gateway()` may call the VeilAI model for gray-zone classification.
- `/api/chat` may call the external chat model when policy allows.
- `BLOCK` is never sent externally.
- `REVIEW` is held if `BLOCK_ON_REVIEW=true`.

## Frontend State Model

Important state variables:

- `curKey`: selected example/scenario key.
- `chatHistory`: displayed chat messages and API conversation input.
- `veilAIEnabled`: current toggle state.
- `activeGateway`: retained gateway result for the lower processing deck.

Important rule:

```text
activeGateway is set only during or after an actual /api/chat request.
```

This prevents pre-analysis from appearing when a user only clicks an example.

## Debugging Notes

Hardcoded demo output:

- Removed static `FINDINGS`, static pipeline arrays, and old hardcoded result blocks.
- The deck now uses gateway API output.

Display cleanup:

- Removed visible legal pill from the header.
- Removed old disclaimer/demo-mode text.
- Removed `local gateway`, `LOCAL`, and bot-message metadata labels.
- Removed the composer `예시` button and replaced it with `Clear`.
- Removed the visible right trace rail.
- Restored the lower processing deck so it opens only after a VeilAI-enabled chat request.
- Removed inline highlight rendering from chat bubbles.

Flip-card bug:

- `처리 로직` became blank after adding animations because `.content-enter` animated `transform` on the flip-card faces.
- The back face depends on `transform: rotateY(180deg)`.
- Fix: do not apply entrance animation to `front` or `back`; animate inner nodes only (`raw`, `cleaned`, `steps`, `ftable`).

No-preanalysis fix:

- Removed UI use of `/api/analyze`.
- Removed startup analysis and example-click analysis.
- Lower deck starts with `analysis-demo collapsed`.
- Lower deck opens only from active `/api/chat`.

Trace-length fix:

- The right trace panel was removed from the visible UI.
- Chat grid height is bounded.
- Chat composer stays in place.

Avoid reintroducing:

- Visible `local gateway`, `LOCAL`, or `PASS · LOCAL` labels in the main chat.
- Static or hardcoded result decks such as the old `87/100` loan example.
- Startup calls that make the page look pre-processed.
- Example-click analysis.
- CSS animation on flip-card face elements.
- Inline colored highlights inside chat messages.

## Verification Commands Used

```bash
python3 -m py_compile server.py veil_gateway.py
curl -s http://127.0.0.1:8088/api/config
curl -s -X POST -H 'Content-Type: application/json' ... http://127.0.0.1:8088/api/chat
curl -s -o /tmp/veil_demo_served.html -w '%{http_code} %{size_download}\n' http://127.0.0.1:8088/
```

Observed checks:

- Served page returns HTTP 200.
- `/api/chat` returns `steps`, `raw`, and `sanitized`.
- The served page contains no UI call to `/api/analyze`.
- Backend files compile with `py_compile`.
- Chat bubbles render escaped plain text.

## Known Constraints

- No Playwright, Selenium, Node, Chromium, Chrome, or Firefox binary is available in this environment, so browser-click automation was not possible here.
- Visual behavior was verified through source inspection and live HTTP/API checks.
- The model names are user-provided config placeholders. Actual availability depends on the OpenAI account/API.

## Current Handoff State

As of this revision:

- Server process is expected at `http://127.0.0.1:8088/`.
- The right trace column is not visible in the current UI.
- The chat composer is intended to stay fixed at the bottom of the chat grid.
- The lower processing deck appears only after an actual VeilAI-enabled chat request.
- `Clear` resets chat, selected example, trace, and deck state.
- Example buttons are in the chat panel and only fill the text area.
- Live model usage is controlled only by `.env`, not by UI labels.

## Revision History

- Revision 1: Captured architecture, files, runtime, API flow, gateway logic, examples, and debugging history.
- Revision 2: Added non-negotiable UI invariants and regression warnings.
- Revision 3: Added current handoff state for future development/debugging.
- Revision 4: Documented the simplified single-column chat UI, removed visible trace rail/deck, and plain chat rendering.
- Revision 5: Documented the clear-button example reset and custom scenario fallback.
- Revision 6: Restored the lower processing deck after chat by removing the permanent CSS display hide.
- Revision 7: Renamed the app entry to `index.html`, moved docs/archive files out of root, removed Python cache, removed stale trace-rail frontend code, and added `DEBUG` logging.

## Next Useful Improvements

- Add a browser-test dependency if this repo will continue UI work.
- Add a small deterministic API test script for `/api/chat` policies.
- Add a UI health check that verifies the deck remains collapsed before send.
- Consider moving inline JS/CSS out of `index.html` if the demo grows further.
