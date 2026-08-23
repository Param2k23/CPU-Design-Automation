# CPU Design Automation Platform

AI-Assisted Verification & Intelligent Debugging.

## Milestone 6: AI-Assisted Verification & Intelligent Debugging

### Architecture & AI Analysis Flow

```
                    Regression
                        |
                        v
                 Simulation Jobs
                        |
              +---------+---------+
              |                   |
           PASSED              FAILED
                                  |
                                  v
                        Evidence Collection
                                  |
                                  v
                     Deterministic Analyzer (Rule-Based)
                                  |
                     +------------+------------+
                     |                         |
               Known failure (>=95% conf)    Unknown/
               & category is known           ambiguous (<95% conf)
                     |                         |
                     |                         v
                     |                   LLM Analyzer (If Enabled)
                     |                         |
                     +------------+------------+
                                  |
                                  v
                         Structured Diagnosis
                                  |
                                  v
                         Persist Analysis (ORIGINAL or REUSED)
                                  |
                                  v
                         Suggested Remediation (Advisory Only)
                                  |
                                  v
                         Optional Revalidate (Triggering Analysis Ref)
                                  |
                                  v
                         New Simulation Attempt
                                  |
                                  v
                         Updated Verification History
```

### Deterministic vs LLM vs Hybrid Analysis

1. **Rule-Based (Deterministic)**: Uses predefined rules to parse simulation output/stderr. Highly reliable for known categories like timeouts or compilation syntax errors.
2. **LLM**: Packages bounded simulation evidence (design/test names, stdout, stderr, compile logs, attempts) and prompts a swappable LLM provider to return structured JSON diagnostics validated using Pydantic.
3. **Hybrid**: Runs deterministic rules first. If confidence is high, returns the deterministic diagnosis immediately to save LLM cost. Otherwise, invokes the LLM analyzer and merges the results.

### Configuration & Environment Variables

Configure the LLM backend with these variables:
- `LLM_ENABLED`: Set to `true` to enable LLM analysis, `false` to disable.
- `LLM_PROVIDER`: Name of the provider (e.g. `openai`, `gemini`).
- `LLM_MODEL`: Model name (e.g. `gpt-4o`).
- `LLM_API_KEY`: API authentication key.

**Note**: If `LLM_ENABLED=false` or no API key exists, the platform fails gracefully and falls back to deterministic analysis.

### API Endpoints

- `POST /jobs/{job_id}/analyze`: Runs analysis. Accepts optional body `{"analyzer": "hybrid"}`.
- `GET /jobs/{job_id}/analyses`: Gets chronological analysis history.
- `GET /jobs/{job_id}/analyses/{analysis_id}`: Gets a specific analysis.
- `POST /jobs/{job_id}/revalidate`: Requeues a job. Accepts optional body `{"triggering_analysis_id": "..."}`.
- `POST /jobs/{job_id}/debug`: Verifies failure, runs analysis, persists it, and optionally revalidates if `{"auto_revalidate": true}` is passed.
- `GET /regressions/{regression_id}/intelligence`: Computes failure clusters, categories, affected designs, top root causes, and recommended actions.

### Running the Demo

Run the Milestone 6 verification demo using:
```bash
python run_milestone6_demo.py
```

### Testing Instructions

Run all tests inside the Docker container environment:
```bash
docker-compose run --rm test
```

### Security Considerations

- **Advisory Recommendations**: AI recommendations are strictly advisory and are **never** automatically applied to the RTL source code.
- **Data Protection**: API keys, credentials, and sensitive filesystem paths are sanitized and filtered before sending to external LLM providers.
