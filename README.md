# Veil AI Demo

Runnable mockup of an agentic financial LLM security gateway.

The chat itself is a normal LLM chat. Alongside it, a **display-only gateway deck**
shows what *would have been* masked or blocked — rule-based detection plus a small
LLM layer — without altering what the model actually receives. One scenario (MNPI)
is a hard circuit break.

## Run

```bash
python3 server.py
```

Open: http://127.0.0.1:8088/

## Configuration (`.env`)

Copy `.env.example` to `.env` and fill in:

```text
OPENAI_API_KEY=          # required for live chat
OPENAI_CHAT_MODEL=...     # main chat model
VEILAI_MODEL=...          # small model for the masking-advisor layer
OPENAI_BASE_URL=https://api.openai.com/v1
LIVE_API_CALLS=true       # false = no external calls
VEILAI_ENABLED=true       # toggles the gateway deck
COMBO_MIN_IDENTIFIERS=4   # quasi-identifiers needed to flag re-identification
HOST=127.0.0.1
PORT=8088
```

`.env` is gitignored — never commit real keys.

## How it works

- **Actual chat is always plain text.** No mask→send→restore round-trip, so there is
  no token key-management problem.
- **The deck is a preview** of what the gateway would do:
  - **Rule layer** (`apply_rule_masking`): phones, RRNs, accounts, cards (Luhn),
    secrets/API keys, named customers, balances (`잔액`), credit grades, delinquency,
    internal hosts, explicit reconstruct attempts.
  - **LLM masking-advisor layer** (free chat only, `VEILAI_MODEL`): decides whether a
    monetary amount is *person-specific* (mask) or *context* (a limit, rate, or company
    financial — keep), and counts *quasi-identifiers* that combine into a
    re-identification risk, masking only the most identifying few.
- **MNPI is the only circuit break** — blocked locally and never sent to the model
  (only while VeilAI is on).

## Files

- `index.html` — chat UI + gateway preview deck.
- `examples.js` — the four demo examples (edit here for quick changes).
- `server.py` — stdlib HTTP server, API routes, LLM calls.
- `veil_gateway.py` — rule masking, circuit break, and LLM-mask application helpers.
- `.env.example` — configuration template.
- `docs/` — product/demo notes. `archive/` — legacy reference HTML.
