## AI Estimation in Carbonly

### Summary

The "Use AI estimate" action does not call an external AI/LLM provider. It creates an estimated activity record using fixed, benchmark-style values, then runs the standard emissions calculation pipeline with existing emission factors.

### Code path

1. Frontend click: `Use AI estimate`
   - `frontend/src/pages/IntegrationsPage.tsx`
2. API call:
   - `POST /api/integrations/{provider}/estimate`
   - `frontend/src/api/integrations.ts`
3. Backend endpoint:
   - `backend/app/api/integrations.py` → `estimate_integration`
4. Estimation logic:
   - `backend/app/services/integration_service.py` → `create_estimated_activity`
5. Emissions calculation:
   - `backend/app/services/emissions.py` → `compute_estimates_for_company`
   - Uses stored emission factors to compute CO2e

### Inputs used

- Provider (aws/gcp/azure)
- Company reporting year
- A fixed benchmark activity record (currently:
  - `activity_type="cloud_compute_hours"`
  - `quantity=8000.0`
  - `unit="hours"`
  - `scope=3`, `scope_3_category="cloud"`)

### How estimates are computed

1. An estimated `ActivityRecord` is created with:
   - `data_quality="estimated"`
   - `assumptions="AI estimated based on company size and industry benchmarks"`
   - `confidence_score=70.0`
2. The standard emissions calculation pipeline runs:
   - It matches the activity record to the best emission factor
   - It computes emissions as `Activity data × Emission factor`
   - Results are stored in `EmissionEstimate` and summarized in `EmissionsSummary`

### Assumptions and limitations

- This is a benchmark-based estimate, not a real-time provider integration.
- It uses a fixed activity record today (placeholder values).
- Accuracy depends on the emission factor table and benchmark assumptions.
- For higher data quality, use "Sync" to connect a provider and measure actual usage.

### Model/provider used

None. No external AI model or LLM is called. The term "AI estimate" currently refers to a benchmark-based heuristic estimate in code.
