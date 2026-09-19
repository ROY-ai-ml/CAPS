# ReRun REST & WebSocket API Specification

## 1. REST Endpoints

### 1.1 Submit Task
`POST /api/tasks`
- **Status Code**: `202 Accepted`
- **Request Body**:
  ```json
  {
    "prompt": "Analyze sales.csv, calculate monthly revenue, and generate sales_chart.png",
    "max_retries": 3,
    "network_policy": "DISABLED"
  }
  ```
- **Response**:
  ```json
  {
    "task_id": "9a0b2ef5-bf9e-43b8-ae0a-247625629f4f",
    "status": "accepted",
    "state": "RECEIVED",
    "message": "Task received and queued for autonomous planning and execution."
  }
  ```

### 1.2 Get Task Detail
`GET /api/tasks/{task_id}`
- **Response**:
  ```json
  {
    "task_id": "9a0b2ef5-bf9e-43b8-ae0a-247625629f4f",
    "prompt": "Analyze sales.csv, calculate monthly revenue, and generate sales_chart.png",
    "state": "COMPLETED",
    "current_attempt": 2,
    "max_retries": 3,
    "created_at": "2026-09-08T11:20:00Z",
    "completed_at": "2026-09-08T11:20:04Z",
    "total_duration_sec": 4.12,
    "validation_passed": true,
    "validation_score": 1.0,
    "artifacts": [
      {
        "filename": "sales_chart.png",
        "file_type": "image/png",
        "file_size_bytes": 27913,
        "storage_path": "/app/artifacts_store/.../sales_chart.png"
      }
    ],
    "code_versions": [
      {
        "version": 1,
        "version_tag": "attempt_1",
        "modification_reason": "Initial generation from plan"
      },
      {
        "version": 2,
        "version_tag": "attempt_2",
        "modification_reason": "Repair KEY_ERROR: Normalized dataframe columns",
        "diff_from_parent": "@@ -14,2 +14,3 @@\n+df.columns = [c.lower() for c in df.columns]"
      }
    ]
  }
  ```

### 1.3 Cancel Task (Human Override)
`POST /api/tasks/{task_id}/cancel`
- **Response**:
  ```json
  {
    "task_id": "9a0b2ef5-bf9e-43b8-ae0a-247625629f4f",
    "status": "cancelled",
    "message": "Task cancellation signal sent."
  }
  ```

### 1.4 Download Artifact
`GET /api/artifacts/{task_id}/{filename}`
- Securely serves binary or text artifacts without exposing host filesystem paths.

---

## 2. Real-Time Streaming APIs

### 2.1 Task WebSocket Stream
`WS /api/ws/tasks/{task_id}`
Pushes real-time execution events directly to connected frontends:
```json
{
  "task_id": "9a0b2ef5-bf9e-43b8-ae0a-247625629f4f",
  "type": "state_transition",
  "state": "EXECUTING",
  "attempt": 1,
  "agent": "master_agent",
  "timestamp": "2026-09-08T11:20:02Z",
  "details": { "reason": "Executing code in sandbox" }
}
```
