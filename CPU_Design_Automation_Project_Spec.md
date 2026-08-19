# CPU Design Automation & AI Debugging Platform
## Detailed Build Specification for an AI Coding Agent

### 1. Project Goal

Build a realistic, locally runnable prototype of a CPU/hardware design automation platform that demonstrates software infrastructure for RTL simulation and verification.

The platform should:

1. Accept RTL simulation/verification jobs through an API.
2. Queue and schedule jobs.
3. Execute simulation workloads in isolated/containerized workers.
4. Use Verilator for RTL simulation.
5. Persist job metadata and results.
6. Handle concurrent jobs, retries, failures, and re-validation.
7. Collect structured logs and metrics.
8. Provide an AI-assisted debugging workflow for failed simulations.
9. Expose observability through Prometheus metrics and Grafana dashboards.
10. Produce a clear demo and measurable benchmark results.

This is a portfolio/recruiting project for a Design Automation & DevOps Software Engineer role. It should prioritize correctness, maintainability, reproducibility, testability, and clear engineering architecture over visual polish.

IMPORTANT:
- Do not fabricate benchmark numbers.
- Resume metrics such as "500+ workloads", "100+ concurrent jobs", "70%+ reduction", "80%+ classification accuracy", and "95%+ reliability" are target goals only until measured.
- Build the system so those metrics can be measured honestly after implementation.
- Do not claim CPU/EDA expertise beyond what the implemented project actually demonstrates.

---

## 2. Recommended Technology Stack

### Backend
- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL

### Job Queue / Coordination
- Redis
- A lightweight worker implementation using Python asyncio/threading or Celery/RQ if justified.
- Prefer a simple architecture that is easy to run locally.

### Hardware Simulation
- Verilator
- SystemVerilog or Verilog RTL
- Make/CMake only where useful

### Containerization
- Docker
- Docker Compose for local orchestration

### Observability
- Prometheus
- Grafana

### AI Debugging
- Provider-agnostic LLM interface.
- The system must work without an LLM API key using a deterministic/mock analyzer.
- If an LLM provider is configured, allow it to analyze simulation logs.
- Never make the entire platform dependent on an external AI API.

### Testing
- PyTest
- FastAPI TestClient
- Integration tests
- Simulation tests

### Optional Frontend
- A minimal Next.js dashboard can be added later.
- Do NOT block the backend/MVP on frontend development.

---

# 3. High-Level Architecture

Implement the following logical architecture:

Client
  |
  v
FastAPI API
  |
  +---- PostgreSQL (job metadata/results)
  |
  +---- Redis (queue/state coordination)
  |
  v
Job Scheduler
  |
  v
Containerized Simulation Workers
  |
  v
Verilator
  |
  +---- RTL source
  +---- Testbench
  +---- Simulation output
  |
  v
Result Collector
  |
  +---- PostgreSQL
  +---- structured logs
  +---- Prometheus metrics
  |
  v
Failure Analyzer
  |
  +---- deterministic analyzer
  +---- optional LLM analyzer
  |
  v
Remediation Recommendation
  |
  v
Re-validation / Retry
  |
  v
Prometheus ---> Grafana

The implementation can initially use Docker Compose with one API service, one scheduler/worker service, PostgreSQL, Redis, Prometheus, and Grafana.

---

# 4. Repository Structure

Create a clean repository approximately like:

cpu-design-automation/
|
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
├── pyproject.toml
|
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── services/
│   │   ├── scheduler/
│   │   ├── workers/
│   │   ├── simulation/
│   │   ├── debugging/
│   │   ├── metrics/
│   │   └── utils/
│   └── tests/
|
├── rtl/
│   ├── alu/
│   ├── register_file/
│   ├── fifo/
│   └── cache/
|
├── testbenches/
│   ├── alu/
│   ├── register_file/
│   ├── fifo/
│   └── cache/
|
├── simulations/
│   ├── configs/
│   ├── scripts/
│   └── results/
|
├── worker/
│   ├── Dockerfile
│   └── entrypoint.sh
|
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       └── dashboards/
|
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── benchmarking.md
│   └── demo.md
|
└── scripts/
    ├── seed_jobs.py
    ├── benchmark.py
    └── run_demo.py

The exact structure can differ if the AI agent has a better maintainable design, but responsibilities must remain separated.

---

# 5. Core Domain Model

Create a SimulationJob model.

Suggested fields:

- id: UUID
- design_name
- test_name
- rtl_path
- testbench_path
- status
- priority
- created_at
- started_at
- completed_at
- worker_id
- attempt_count
- max_retries
- exit_code
- runtime_ms
- stdout
- stderr
- failure_category
- failure_summary
- remediation
- result_artifact_path

Job statuses:

QUEUED
SCHEDULED
RUNNING
PASSED
FAILED
RETRYING
CANCELLED

Failure categories should include examples such as:

- COMPILE_ERROR
- ASSERTION_FAILURE
- TIMEOUT
- SIMULATION_ERROR
- INFRASTRUCTURE_ERROR
- UNKNOWN

---

# 6. API Requirements

Implement FastAPI endpoints.

### Health

GET /health

Returns service health.

### Submit Job

POST /jobs

Example:

{
  "design_name": "alu",
  "test_name": "overflow_test",
  "priority": "high",
  "max_retries": 2
}

Returns job ID and status.

### Get Job

GET /jobs/{job_id}

Return job metadata, status, runtime, attempts, and result.

### List Jobs

GET /jobs

Support filters:
- status
- design
- priority
- date
- limit

### Retry Job

POST /jobs/{job_id}/retry

Only failed jobs should be retryable.

### Cancel Job

POST /jobs/{job_id}/cancel

Cancel queued jobs. Running cancellation can be implemented later.

### Job Logs

GET /jobs/{job_id}/logs

Return structured simulation logs.

### Debug Analysis

POST /jobs/{job_id}/analyze

Run failure analysis and return:
- category
- summary
- suspected root cause
- evidence
- remediation recommendation
- confidence

### Revalidate

POST /jobs/{job_id}/revalidate

Create a new validation attempt after remediation.

### Metrics

GET /metrics

Expose Prometheus-compatible metrics.

---

# 7. Scheduler Requirements

Implement a scheduler that:

1. Pulls queued jobs.
2. Respects priority.
3. Assigns jobs to available workers.
4. Limits concurrency.
5. Tracks worker state.
6. Handles worker failures.
7. Supports retries.
8. Records scheduling latency.
9. Prevents duplicate execution of the same job.
10. Gracefully shuts down.

Worker states:

AVAILABLE
BUSY
FAILED
DRAINING

Create a worker registry.

At minimum, support configurable concurrency, e.g.:

WORKER_CONCURRENCY=4

Do not hard-code a specific benchmark.

---

# 8. Simulation Worker Requirements

A worker must:

1. Receive a simulation job.
2. Resolve RTL and testbench.
3. Run Verilator.
4. Capture stdout/stderr.
5. Capture exit code.
6. Enforce timeout.
7. Store artifacts.
8. Return structured results.
9. Mark the worker available afterward.
10. Handle crashes without corrupting job state.

Example command conceptually:

verilator --binary --timing <rtl> <testbench>

The exact command must be validated against the chosen RTL/testbench implementation.

The worker should never execute arbitrary user-provided shell commands.

Use controlled command construction and subprocess argument arrays rather than shell=True.

---

# 9. RTL Designs

Create several simple but legitimate RTL examples.

At minimum:

1. ALU
   - add
   - subtract
   - AND
   - OR
   - XOR
   - overflow/edge cases

2. FIFO
   - enqueue
   - dequeue
   - full
   - empty

3. Register File
   - read
   - write
   - reset

4. Small Cache or equivalent memory component

The designs should be simple enough to understand during an interview.

---

# 10. Testbenches

Create automated testbenches for each RTL component.

Include:

- passing tests
- intentionally failing tests
- edge cases
- malformed/compile-failure scenario if safe
- timeout scenario if practical

The failing tests are important because the AI debugging pipeline needs realistic failure logs.

Each test should produce deterministic output.

---

# 11. Failure Detection

When a simulation exits non-zero or violates an expected assertion:

1. Mark job FAILED.
2. Parse stdout/stderr.
3. Determine failure category.
4. Store evidence.
5. Trigger optional AI analysis.
6. Generate remediation recommendation.
7. Optionally retry.
8. Record every attempt.

Do not classify failures solely using an LLM.

Build deterministic rules first.

Example:

if log contains "syntax error":
    COMPILE_ERROR

if log contains "assert":
    ASSERTION_FAILURE

if process exceeds timeout:
    TIMEOUT

otherwise:
    UNKNOWN

---

# 12. AI-Assisted Debugging

Create an abstraction:

FailureAnalyzer

with implementations:

1. RuleBasedFailureAnalyzer
2. LLMFailureAnalyzer

The rule-based implementation must always work.

The LLM implementation should receive:

- design name
- test name
- failure category
- relevant logs
- RTL snippet where appropriate
- testbench snippet where appropriate

Return structured JSON:

{
  "category": "ASSERTION_FAILURE",
  "summary": "...",
  "suspected_root_cause": "...",
  "evidence": ["...", "..."],
  "recommended_fix": "...",
  "confidence": 0.84
}

Do not allow an LLM to directly execute arbitrary code or commands.

---

# 13. Automated Recovery / Re-validation

Implement:

FAILED
  |
  v
Analyze
  |
  v
Recommendation
  |
  v
Retry/Revalidate
  |
  v
Simulation
  |
  +---- PASS
  |
  +---- FAIL

The first implementation can simply re-run the job with the recommended remediation recorded.

Do NOT automatically modify source code unless a safe, deterministic mechanism is later added.

This keeps the system safe and reproducible.

---

# 14. Observability

Use Prometheus metrics.

At minimum:

simulation_jobs_total
simulation_jobs_success_total
simulation_jobs_failed_total
simulation_job_duration_seconds
simulation_queue_depth
simulation_retries_total
worker_jobs_active
worker_utilization
failure_analysis_total
failure_analysis_accuracy
job_completion_reliability

Use labels carefully to avoid high-cardinality metrics.

Do not put job IDs into Prometheus labels.

Create Grafana dashboards showing:

1. Total jobs
2. Success/failure rate
3. Queue depth
4. Average/p95 job latency
5. Active workers
6. Worker utilization
7. Retry rate
8. Failure categories
9. AI analysis results

---

# 15. Benchmarking

Create scripts/benchmark.py.

The benchmark must measure:

- total jobs submitted
- successful jobs
- failed jobs
- throughput
- average latency
- p95 latency
- maximum concurrency
- retry count
- worker utilization
- failure classification accuracy
- end-to-end completion reliability

Run controlled workloads such as:

10 jobs
50 jobs
100 jobs
500 jobs

Do not claim 500+ or 100+ concurrent execution unless the local environment actually demonstrates it.

For "manual effort reduction", define a reproducible baseline, for example:

Manual workflow:
human inspects logs + identifies failure + decides next action.

Automated workflow:
system classifies and produces remediation recommendation.

Measure time saved from repeated benchmark trials rather than inventing a percentage.

---

# 16. Reliability Testing

Create tests for:

- worker crash
- Redis unavailable
- PostgreSQL unavailable
- simulation timeout
- malformed RTL
- failed test
- duplicate job submission
- retry exhaustion
- scheduler restart
- worker restart

The system should fail gracefully.

---

# 17. Security / Quality Requirements

Follow these rules:

- No shell=True.
- Validate API input.
- Limit log size returned through API.
- Never expose secrets.
- Use environment variables for configuration.
- Never send database credentials to workers unnecessarily.
- Do not allow arbitrary command execution.
- Sanitize file paths.
- Use non-root Docker containers where practical.
- Add structured logging.
- Add unit tests for core services.
- Add integration tests for job lifecycle.
- Add type hints.
- Keep modules small and maintainable.

---

# 18. Docker Compose

Provide one command to start the system:

docker compose up --build

Expected services:

api
scheduler/worker
postgres
redis
prometheus
grafana

The exact service split can be adjusted.

Document ports and health checks.

---

# 19. Developer Commands

Create Makefile targets:

make setup
make test
make lint
make run
make benchmark
make demo
make down

If a command is unavailable on a platform, document the alternative.

---

# 20. Demo Workflow

The README must include a reproducible demo:

1. Start Docker Compose.
2. Check /health.
3. Submit an ALU simulation.
4. Show QUEUED.
5. Show RUNNING.
6. Show PASSED.
7. Submit an intentionally failing test.
8. Show FAILED.
9. Run /analyze.
10. Show failure classification.
11. Show root-cause hypothesis.
12. Show remediation recommendation.
13. Revalidate.
14. Show result.
15. Open Grafana.
16. Show queue depth, latency, worker utilization, and failure metrics.
17. Run benchmark.py.

The demo should be achievable by a new developer following README instructions.

---

# 21. Documentation

Create:

docs/architecture.md
- architecture diagram
- component responsibilities
- data flow
- failure flow

docs/api.md
- endpoint documentation
- example requests/responses

docs/benchmarking.md
- benchmark methodology
- metrics definitions
- how to reproduce results

docs/demo.md
- exact demo commands

README.md should contain:
- project overview
- why the project exists
- architecture
- technology stack
- quick start
- demo
- tests
- benchmark
- observability
- AI debugging
- limitations
- future work

---

# 22. Definition of Done for MVP

The MVP is complete when all of the following work:

[ ] FastAPI starts successfully.
[ ] PostgreSQL stores jobs.
[ ] Redis handles queue/state coordination.
[ ] Worker executes Verilator simulations.
[ ] At least 3 RTL designs work.
[ ] Passing simulations become PASSED.
[ ] Failing simulations become FAILED.
[ ] Logs are persisted/retrievable.
[ ] Retries work.
[ ] Concurrent jobs work.
[ ] Failure categories are generated deterministically.
[ ] AI analyzer interface works with a mock provider.
[ ] Optional LLM provider can be plugged in.
[ ] Re-validation workflow works.
[ ] Prometheus metrics are exposed.
[ ] Grafana dashboard loads.
[ ] Benchmark script works.
[ ] Unit tests pass.
[ ] Integration tests pass.
[ ] Docker Compose starts the complete system.
[ ] README can reproduce the demo.

---

# 23. Resume Metric Targets

These are NOT claims until measured.

Potential target areas:

- 500+ total simulation workloads
- 100+ concurrent validation jobs
- 70%+ reduction in manual simulation/debugging effort
- 80%+ failure classification accuracy
- 95%+ job completion reliability

The agent must build benchmark tooling capable of measuring these.

If actual numbers differ, use actual numbers.

---

# 24. Development Strategy

Implement incrementally.

PHASE 1:
Repository + FastAPI + database + health endpoint.

PHASE 2:
Redis + job queue + scheduler.

PHASE 3:
Docker worker + Verilator.

PHASE 4:
RTL designs + testbenches.

PHASE 5:
Concurrent execution + retries + result storage.

PHASE 6:
Failure classification.

PHASE 7:
AI debugging abstraction.

PHASE 8:
Prometheus + Grafana.

PHASE 9:
Benchmarking.

PHASE 10:
Testing + security + documentation + polish.

After every phase:
- run tests
- verify the application starts
- avoid accumulating broken features
- update README where necessary.

Do not implement everything in one giant untested change.

---

# 25. Important AI Coding-Agent Instructions

You are the primary implementation agent.

Before writing significant code:

1. Inspect the repository.
2. Determine whether any existing files should be preserved.
3. Create a concise implementation plan.
4. Implement the smallest working slice.
5. Run tests.
6. Fix errors.
7. Continue to the next phase.

Do not rewrite working components unnecessarily.

Do not introduce technologies merely because they sound impressive.

Prefer simple, explicit Python over excessive abstraction.

Every major component must have a clear responsibility.

Do not fabricate successful benchmark results.

If a dependency is unavailable, document it and provide a fallback.

The final project should be runnable by another engineer from a clean machine using the documented setup.

---

# 26. First Milestone

The first milestone should deliver:

- repository structure
- Python environment
- FastAPI
- PostgreSQL
- Redis
- Docker Compose
- Job model
- POST /jobs
- GET /jobs/{id}
- GET /health
- basic queue
- one worker
- one RTL component
- one passing simulation
- one failing simulation
- persisted results
- basic tests

Do not start with Grafana, AI, or frontend.

Get the simulation/job lifecycle working first.

