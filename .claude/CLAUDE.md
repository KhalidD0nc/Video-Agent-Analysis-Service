# CoachAI — Refactor Progress Tracker

Branch: `refactor/coachai-package`
Goal: Extract a clean `src/coachai/` Python package so `modal_app.py` becomes a thin HTTP adapter.

---

## Checklist

- [ ] 0. Write this tracker to `.claude/CLAUDE.md`
- [ ] 1. Create branch `refactor/coachai-package`
- [ ] 2. Delete `model/impl/gsf.py` + `gsm.py` (dead code, confirmed unused)
- [ ] 3. Add `.env` to `.gitignore` + create `.env.example`
- [ ] 4. Create `src/coachai/` skeleton + `pyproject.toml`
- [ ] 5. Create `coachai/config.py` (all scattered constants)
- [ ] 6. Create `coachai/reporting/prompts.py` (extract inline prompt strings)
- [ ] 7. Create `coachai/inference/io.py` → delete `util/io.py` + `util/dataset.py`
- [ ] 8. Create `coachai/ingestion/downloader.py` (video download logic)
- [ ] 9. Create `coachai/inference/dataset.py` (3 inference classes from frame.py)
- [ ] 10. Create `coachai/inference/postprocess.py` (NMS + event extraction from eval.py)
- [ ] 11. Create `coachai/inference/engine.py` (T-DEED wrapper)
- [ ] 12. Create `coachai/analysis/timeline.py` (frame→timestamp, JSON→CSV)
- [ ] 13. Create `coachai/analysis/cleaner.py` (merge + dedup logic)
- [ ] 14. Create `coachai/reporting/gemini_client.py` (Gemini API wrapper)
- [ ] 15. Create `coachai/pipeline.py` (single orchestrator)
- [ ] 16. Create `run_local.py` (thin CLI) + smoke test
- [ ] 17. Rewrite `modal_app.py` as thin wrapper (~80 lines) ⚠️ production
- [ ] 18. Delete `inference.py`, `run_pipeline.py`, `run_but_by_youtube.py`
- [ ] 19. Add empty test stubs in `tests/`
- [ ] 20. Merge `refactor/coachai-package` → `main`

---

## Target Structure

```
src/
└── coachai/
    ├── __init__.py
    ├── config.py
    ├── pipeline.py
    ├── ingestion/
    │   ├── __init__.py
    │   └── downloader.py
    ├── inference/
    │   ├── __init__.py
    │   ├── engine.py
    │   ├── dataset.py
    │   ├── postprocess.py
    │   └── io.py
    ├── analysis/
    │   ├── __init__.py
    │   ├── cleaner.py
    │   └── timeline.py
    └── reporting/
        ├── __init__.py
        ├── gemini_client.py
        └── prompts.py
```

---

## Key Rules
- One step = one commit
- No behavior changes — structure only
- Steps 9, 10, 11 touch files used by inference — verify with import check after each
- Step 17 is production (`modal_app.py`) — do last, verify with `modal run` dry-run before deploying
- Do NOT merge to `main` until step 17 is verified
