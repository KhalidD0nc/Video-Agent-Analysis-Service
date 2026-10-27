# HTTP API

Use the endpoint URLs returned by your Modal deployment. Each function has its own URL; the examples use shell variables rather than a shared base URL.

## Submit an asynchronous analysis

```bash
export COACHAI_SUBMIT_URL="https://YOUR-SUBMIT-ENDPOINT.modal.run"
export COACHAI_STATUS_URL="https://YOUR-STATUS-ENDPOINT.modal.run"
curl --fail-with-body "$COACHAI_SUBMIT_URL" \
  -H 'Content-Type: application/json' \
  -d '{"video_url":"https://example.com/match.mp4","primary_team":"Team A"}'
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `video_url` | string | empty | Direct or supported download URL |
| `video_path` | string | empty | Existing file accessible inside the service container |
| `primary_team` | string | empty | Optional coaching perspective |
| `inference_threshold` | number | `0.3` | Detection confidence threshold |
| `skip_gemini` | boolean | `false` | Extract events without generating reports |

Provide `video_url` or `video_path`. A local path on your laptop is not accessible to a remote container. The current adapter returns an error object if both fields are absent.

```json
{
  "status": "submitted",
  "job_id": "fc-EXAMPLE",
  "message": "Poll GET /status?job_id=<job_id> for results."
}
```

## Poll the job

```bash
curl --fail-with-body --get "$COACHAI_STATUS_URL" \
  --data-urlencode "job_id=fc-EXAMPLE"
```

| State | Response |
| --- | --- |
| Pending | HTTP 202 with `status: "pending"` |
| Completed | `status: "completed"` and a `result` object |
| Failed | `status: "error"` and a message |

A completed result contains `status`, `stages`, `timeline_csv`, and `pipeline_duration_seconds`. With reporting enabled it also contains `tactical_report_json` and `comprehensive_analysis_md`. The `primary_team` field is included when a non-empty team is supplied. Both report fields are strings. Inspect the returned content for reporting errors; job completion alone does not prove valid Gemini output. Some adapter errors are returned as JSON error objects with HTTP 200, so check the body as well as the HTTP status.

## Other endpoint functions

- **`analyze` (POST):** accepts `video_url`, `primary_team`, `inference_threshold`, and `skip_gemini`; returns the pipeline result synchronously. Intended for short videos and testing.
- **`health` (GET):** returns `status`, service name, configured models, and timestamp. This endpoint does not load checkpoints or run inference.

## Modal setup

The adapter uses a volume named `coachAI-weights` and a Modal secret named `gemini-api-key` containing `GEMINI_API_KEY`. Install the Modal CLI in your development environment and configure its authentication before using the commands below.

Prepare the `weights/` layout from the README, then upload each prepared directory:

```bash
modal volume create coachAI-weights
modal volume put coachAI-weights ./weights/checkpoints /checkpoints
modal volume put coachAI-weights ./weights/config /config
modal volume put coachAI-weights ./weights/class_data /class_data

# Temporary development endpoint; may build an image and use GPU/API resources
modal serve modal_app.py

# Explicit persistent deployment
modal deploy modal_app.py
```

The checked-in app and volume names are shared defaults. Separate staging and production deployments need distinct Modal environment configuration and independently verified endpoint URLs.

## Manual live checks

The **Live Endpoint Checks** workflow requires repository variables `MODAL_HEALTH_URL`, `MODAL_SUBMIT_URL`, and `MODAL_STATUS_URL`. Its input clip must exist inside the mounted weights volume. Choose the team perspective when dispatching it. Running this workflow starts a real analysis job and can incur provider usage; ordinary pushes and pull requests run only offline checks.
