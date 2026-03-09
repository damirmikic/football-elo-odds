# Football Elo Odds App — Complete Revamp Plan

## Why a revamp is needed

The current app works for many core calculations, but its structure makes it hard to reason about and easy to break:

- `app.py` is a very large monolithic Streamlit script (2,376 lines), mixing UI rendering, data loading, scraping, business logic, and error handling in one file.
- Tests currently focus on utility modules (`odds.py`, `ev_calculator.py`, `kambi_client.py`) while the Streamlit entrypoint has effectively no coverage.
- Runtime behavior depends on external websites/API responses and HTML shape, so breakage is likely without a resilient adapter layer and clear fallback states.

## Target architecture (clean-slice design)

Revamp into a layered application where each layer has one reason to change:

```text
src/
  football_elo_odds/
    domain/                # Pure business logic, deterministic, no I/O
      models.py            # dataclasses / pydantic models
      odds_engine.py       # probabilities, EV, margin models
      mapping.py           # team/league canonicalization

    services/              # Use-cases orchestrating domain + repos/clients
      match_analysis.py
      market_projection.py
      team_lookup.py

    adapters/              # I/O boundaries
      providers/
        soccer_rating.py   # scraping/parsing from soccer-rating
        kambi.py           # Kambi integration
      repositories/
        league_stats_repo.py
        team_mapping_repo.py
      cache/
        cache_manager.py

    app/
      ui/
        streamlit_app.py   # only UI composition/state/events
      api/
        main.py            # optional FastAPI for future web/mobile consumers

    observability/
      logging.py
      telemetry.py

    settings.py            # env-based config (pydantic-settings)
```

## Revamp principles

1. **UI is a shell, not the brain**
   - Move all calculations and data orchestration out of Streamlit callbacks.
2. **Typed contracts everywhere**
   - Define request/response models for every external provider and internal use-case.
3. **Provider adapters are replaceable**
   - Scraper/API specifics stay inside adapters; domain/services remain stable.
4. **Graceful degradation by design**
   - If one source fails, UI should still render with clear status + partial functionality.
5. **Test pyramid enforcement**
   - Unit tests for domain, contract tests for adapters, integration tests for use-cases, smoke tests for UI.

## Error-handling redesign

### Current pain
- Network and parsing concerns are often managed inline in UI flow.
- Hard to distinguish user-facing recoverable errors from developer/actionable failures.

### Proposed model
- Introduce a unified `AppError` hierarchy:
  - `ExternalServiceError`
  - `DataValidationError`
  - `NotFoundError`
  - `ConfigurationError`
- Services return either typed success payloads or typed errors mapped to user-safe messages.
- Add retry strategy + circuit-breaker for unstable providers.
- Add structured logs with correlation IDs per analysis request.

## Data and configuration redesign

- Split static giant config maps into versioned data files in `data/` (or sqlite) with schema validation.
- Introduce startup validation:
  - required files present
  - schema checks pass
  - external provider health checks
- Use environment-specific settings (`dev`, `test`, `prod`) to avoid hardcoded runtime behavior.

## UX revamp goals

- Replace one massive page with a stepper/workflow:
  1. Select league + match
  2. Validate data sources
  3. View projected probabilities
  4. Compare bookmaker lines + EV
  5. Export/share report
- Add clear loading/error skeleton states for each section.
- Add diagnostics panel (expandable) showing data freshness and source status.

## Incremental migration plan (8 weeks)

### Phase 0 (Week 1): Stabilize & baseline
- Add telemetry/logging baseline and error boundaries around existing app.
- Capture current behavior with golden tests for key calculation outputs.

### Phase 1 (Week 2–3): Extract domain
- Move pure calculation logic from `app.py` into `domain/*`.
- Add strict unit tests and mutation-resistant fixtures.

### Phase 2 (Week 4): Extract provider adapters
- Wrap scraping/API calls behind interfaces.
- Add contract tests using recorded fixtures.

### Phase 3 (Week 5): Build service layer
- Introduce use-cases consumed by UI.
- Remove direct network/data access from Streamlit file.

### Phase 4 (Week 6): Rebuild UI composition
- Replace monolithic UI flow with section components and predictable state model.
- Add smoke tests for major user journeys.

### Phase 5 (Week 7): Hardening
- Performance profile slow paths.
- Add cache invalidation and fallback strategy.
- Improve error copy and observability dashboards.

### Phase 6 (Week 8): Cutover
- Feature flag old/new paths.
- Shadow-run and compare outputs.
- Remove old path once parity threshold is met.

## Definition of done for revamp

- `app.py` reduced to thin composition entrypoint (<300 LOC target).
- Domain and service layers have >90% coverage.
- No untyped dictionaries crossing module boundaries.
- Provider failures do not crash the UI.
- P95 end-to-end analysis latency < 2.0s with warm cache.

## Immediate next actions (this week)

1. Create package scaffolding under `src/football_elo_odds/`.
2. Extract first use-case: match outcome probability calculation.
3. Add typed models for market inputs/outputs.
4. Introduce centralized error mapper for Streamlit toasts/panels.
5. Add CI gates: `ruff`, `mypy`, `pytest --cov` thresholds by layer.

