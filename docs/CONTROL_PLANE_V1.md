# Wasabi Control Plane v1

## Goal

Run coding-agent tasks in isolated workspaces through a durable workflow. Show every agent's status, tool activity, handoffs, failures, and final artifacts in a dashboard.

The one-day goal is a working vertical slice, not a claim of full production readiness.

## Locked stack

- **Orchestration:** Inngest Python SDK. Use durable steps, retry policy, cancellation, concurrency limits, and Inngest run traces.
- **Coding harness:** the existing Wasabi Python agent behind an adapter. Do not replace its security and tool logic during the first build.
- **Workspace provider:** Daytona for cloud sandboxes. Keep a provider interface and a local Docker implementation for development without cloud credentials.
- **State:** PostgreSQL for product state and the event ledger.
- **API and worker:** FastAPI + Inngest Python SDK.
- **Dashboard:** Next.js. The dashboard consumes the control-plane API and a Server-Sent Events stream.
- **Observability:** Inngest run traces plus structured agent events. Add OpenTelemetry spans and metrics after the vertical slice works.

Do not add Temporal, Celery, a second queue, Kubernetes, RAG, fine-tuning, or RL to v1.

## Workflow

1. The user submits a repository and task. The API creates a run record and emits `wasabi/run.requested`.
2. Inngest validates the request and reserves a bounded execution slot.
3. The workspace provider creates or retrieves the workspace for the run. Persist its provider ID before continuing.
4. The workflow prepares a task branch and records the starting commit.
5. The **planner** creates a structured plan and handoff artifact.
6. The **implementer** works through Wasabi's scoped tools. Persist every model response, tool intent, tool result, and agent event.
7. The **reviewer** inspects the diff and runs approved checks. It does not edit files in v1.
8. The workflow stores the diff, test output, summary, usage metrics, and final workspace reference.
9. The user reviews the result. Do not merge or deploy automatically.
10. Apply a bounded cleanup policy. Keep a workspace only when the run is resumable or the user requests retention.

Agent roles are sequential stages in v1. Separate runs can execute concurrently in separate workspaces. Do not let multiple agents edit the same workspace concurrently.

## Durability: a critical implementation detail

Inngest makes workflow steps durable. It does **not** automatically make a single long-running `Wasabi.chat()` loop resumable between arbitrary model and tool operations.

Wasabi's current `chat()` method performs model calls and tool calls inside one loop. Split the loop into explicit resumable transitions:

- `infer_turn`: make one model request and persist the assistant response and tool-call intents.
- `execute_tool_call`: execute one validated tool call under a stable ID.
- `record_tool_result`: persist the structured result and append it to the session transcript.
- Continue with the next inference turn until the model returns a final answer or the run reaches a limit.

Use stable Inngest step IDs such as `infer-turn-0003` and `tool-turn-0003-call-abc`. Persist the transcript and tool-call ledger in PostgreSQL, not only in worker memory or a VM filesystem.

Every side effect must have an idempotency strategy. Persist a tool action ID before execution and record its result. For tools that call external systems, use the external system's idempotency support when available. Do not claim exactly-once side effects: a crash can occur after an external action succeeds but before the workflow records its result.

The first tested recovery point is a completed durable step. Recovery in the middle of an individual tool's external side effect needs its own idempotency/reconciliation behavior.

## Minimal data model

### `runs`

- `id`, `status`, `request_text`, `repository_url`, `base_commit`
- `current_stage`, `workspace_provider`, `workspace_id`
- `started_at`, `finished_at`, `cancel_requested_at`
- `final_summary`, `failure_reason`, `trace_id`

### `agent_runs`

- `id`, `run_id`, `role`, `status`, `attempt`
- `session_id`, `started_at`, `finished_at`

### `run_events`

- `id`, `run_id`, `agent_run_id`, `sequence`
- `event_type`, `payload_json`, `created_at`

### `handoffs`

- `id`, `run_id`, `from_agent_run_id`, `to_agent_role`
- `schema_version`, `payload_json`, `created_at`

### `tool_actions`

- `idempotency_key`, `run_id`, `agent_run_id`, `tool_name`
- `status`, `input_hash`, `result_json`, `started_at`, `finished_at`

### `artifacts`

- `id`, `run_id`, `kind`, `uri`, `sha256`, `metadata_json`

Use database transactions and unique constraints where they protect task identity and tool-action identity.

## Handoff contract

A handoff is a versioned artifact, not an unstructured message alone. It contains:

- objective and acceptance criteria
- task plan and constraints
- allowed tools and permissions
- workspace ID and expected Git revision
- files changed or files to inspect
- evidence collected so far
- unresolved questions and known risks

The receiver validates the workspace and revision before it acts.

## Run states

`queued -> preparing -> planning -> implementing -> verifying -> awaiting_review -> completed`

Failure and control states: `retrying`, `blocked`, `failed`, `cancel_requested`, `cancelled`.

Status updates must follow valid transitions. Retries must not create a second logical run.

## Dashboard v1

1. **Runs:** status, task, age, current stage, retry count, workspace state.
2. **Run detail:** agent swimlane, durable-step timeline, live tool events, handoff artifacts, errors and trace identifiers.
3. **Artifacts:** Git diff, test output, final summary and links to the workspace when safe.
4. **Controls:** create run, cancel run, retry failed run, approve retention or cleanup.

Use Server-Sent Events for a simple live feed. The persisted `run_events` table is the source of truth; the stream is only a transport.

## Safety boundaries

- One workspace per logical run; isolate runs from each other.
- Never expose provider credentials to the model or the target repository.
- Keep cloud-provider credentials only in the control plane.
- Apply CPU, memory, disk, wall-time, concurrency, and model-cost limits.
- Start with a fixed set of scoped tools. Do not add unrestricted host shell access.
- Make workspace cleanup explicit and observable.
- Treat repository content and tool output as untrusted input.
- Require review before merge, release, or deployment.

## One-day acceptance criteria

- [ ] Submit a task in the dashboard and see a persisted run.
- [ ] Observe planner, implementer, and reviewer stages.
- [ ] See tool calls, results, errors, and handoffs in the run timeline.
- [ ] Run inside a cloud sandbox, or use the local Docker provider when credentials are unavailable.
- [ ] Force a failure after at least one completed step and show that retry reuses the completed step result.
- [ ] Resume a saved agent transcript without losing completed tool results.
- [ ] Avoid re-running completed tool actions when the workflow retries.
- [ ] Collect a Git diff and real test output.
- [ ] Cancel a run and verify cleanup or retained-workspace state.
- [ ] Document known limits, setup, a demo script, and the recovery semantics.

## What to explain in an interview

- **Workflow durability vs agent-session durability:** Inngest persists workflow steps; Wasabi must persist its conversation and tool ledger.
- **At-least-once delivery vs exactly-once effects:** retries can repeat a side effect unless the action is idempotent or reconciled.
- **Control plane vs execution plane:** the API/orchestrator authorizes and observes work; the isolated workspace executes code.
- **Handoff vs shared mutable state:** structured versioned artifacts reduce ambiguity between agents.
- **Observability vs logging:** events describe what happened; traces connect causal work; metrics describe frequency and latency.
- **Security model:** the model requests actions, but trusted code validates permissions and executes bounded capabilities.

## Scope boundary

V1 is a single-user engineering demo. It is not yet a multi-tenant production service. Kubernetes, parallel agents editing one workspace, fine-tuning, RL, retrieval memory, automatic merging, and self-modifying policies are follow-up work only after the recovery and isolation tests pass.
