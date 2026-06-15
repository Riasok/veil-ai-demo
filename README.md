# Veil AI Demo

Runnable demo for an agentic financial LLM security gateway.

## Run

```bash
python3 server.py
```

Open:

```text
http://127.0.0.1:8088/
```

The old `/veil_demo_v3.html` path is kept as a compatibility alias.

## Main Files

- `index.html`: chat UI and lower gateway processing deck.
- `server.py`: local HTTP server and API routes.
- `veil_gateway.py`: rule masking, VeilAI prompt contract, policy merge, and restore logic.
- `.env.example`: runtime configuration template.
- `docs/`: product and demo planning notes.
- `archive/`: legacy reference file kept out of the runtime path.
