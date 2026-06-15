# Veil AI Demo — Implementation Notes

Last revised: 2026-06-15

## What this is

A runnable **mockup** of an agentic financial LLM security gateway. The product
story: an employee chats normally; a gateway layer shows what sensitive data
*would* be masked or blocked before an external model sees it.

Key design decision (mockup): **the actual chat is always sent as plain text.**
The gateway output is a *display-only preview* — it never rewrites what the model
receives. This removes the mask→send→return→demask token key-management problem.

## Architecture

```
user message ─┬─► gateway_preview()  → deck (what WOULD be masked/blocked)
              └─► plain LLM chat      → assistant reply
```

- **Chat path** (`server.py:handle_chat`)
  - Built-in examples: a one-shot LLM call reproduces the example's reference
    answer with slight variation (`build_example_prompt`).
  - Free chat: normal multi-turn conversation (`build_plain_chat_prompt`).
  - **MNPI** scenario: circuit break — blocked locally, never sent (only while
    VeilAI is on). It is the *only* circuit break.
  - Live calls require `LIVE_API_CALLS=true` + `OPENAI_API_KEY`.

- **Gateway preview** (`gateway_preview`) — display only:
  - **Rule layer** (`veil_gateway.apply_rule_masking`): deterministic regex/checksum
    detection (phones, RRNs, accounts, cards w/ Luhn, secrets, known names, generic
    names in context, `잔액` balances, credit grades, delinquency, internal hosts,
    explicit reconstruct attempts → BLOCK).
  - **LLM masking-advisor** (`detect_masking_advice`, free chat only, uses
    `VEILAI_MODEL`): one nano call returning
    - `sensitive_amounts` — person-specific amounts to mask (excludes limits, rates,
      and company financials), and
    - quasi-identifier combination → `reidentifiable` + `reid_mask`; if the count
      reaches `COMBO_MIN_IDENTIFIERS`, the most identifying few are masked.
    The prompt embeds all four demo scenarios as few-shot examples so masking is
    consistent with the demo (incl. the 법인+생년+직책 loan combination).

## Toggle / examples behavior

- **VeilAI ON/OFF** only shows/hides the deck — the chat works the same either way.
- Examples fill the input; sending an example holds a 2–3s "processing" beat before
  the deck appears. Editing a loaded example reverts it to free (`custom`) chat.
- Examples live in `examples.js` (`name`, `who`, `raw`, `answer`, `circuitBreak`).

## API

- `GET /api/config` — runtime config (used by the UI to init the toggle).
- `POST /api/chat` — main path; returns the preview deck fields + `assistant`,
  `policy`, `circuit_break`.
- `POST /api/analyze` — preview only (debug; not used by the UI).

## Security notes

- `.env` is gitignored and the static server refuses to serve dotfiles / source
  (`SERVABLE_SUFFIXES` allowlist in `server.py`). Never commit real keys.
- BLOCK placeholders are irreversible; the preview's restore_map is illustrative
  only (nothing is restored, since nothing is actually masked on the wire).

## Verify

```bash
python3 -m py_compile server.py veil_gateway.py
curl -s http://127.0.0.1:8088/api/config
```
