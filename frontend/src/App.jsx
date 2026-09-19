import React, { useState, useEffect, useRef } from "react";
import Navbar from "./components/Navbar";
import TaskInput from "./components/TaskInput";
import StatePipeline from "./components/StatePipeline";
import LiveLogs from "./components/LiveLogs";
import CodeViewer from "./components/CodeViewer";
import MetricsPanel from "./components/MetricsPanel";
import ValidationDeliverables from "./components/ValidationDeliverables";
import BenchmarkPanel from "./components/BenchmarkPanel";
import { submitTask, fetchTask, fetchTasks, cancelTask, WS_BASE } from "./services/api";

export default function App() {
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [taskData, setTaskData] = useState(null);
  const [events, setEvents] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [stats, setStats] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showBenchmark, setShowBenchmark] = useState(false);

  const wsRef = useRef(null);

  // Load platform statistics
  useEffect(() => {
    fetchTasks()
      .then((res) => {
        setStats(res.stats);
        // Load latest task if present
        if (res.tasks && res.tasks.length > 0 && !currentTaskId) {
          const latest = res.tasks[0];
          setCurrentTaskId(latest.id);
        }
      })
      .catch((err) => console.error("Failed to load initial tasks:", err));
  }, []);

  // Fetch task details when currentTaskId changes
  useEffect(() => {
    if (!currentTaskId) return;

    fetchTask(currentTaskId)
      .then((data) => setTaskData(data))
      .catch((err) => console.error("Error loading task:", err));

    // Connect WebSocket
    if (wsRef.current) {
      wsRef.current.close();
    }

    const wsUrl = `${WS_BASE}/tasks/${currentTaskId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
    };

    ws.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        setEvents((prev) => [...prev, payload]);

        // Refresh task data if state transition or completion
        if (
          payload.type === "state_transition" ||
          payload.type === "code_generated" ||
          payload.type === "execution_finished" ||
          payload.type === "validation_result" ||
          payload.type === "task_completed" ||
          payload.type === "task_failed" ||
          payload.type === "task_cancelled"
        ) {
          fetchTask(currentTaskId).then((updated) => setTaskData(updated));
        }
      } catch (err) {
        console.error("Error parsing WS event:", err);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    return () => {
      if (ws) ws.close();
    };
  }, [currentTaskId]);

  const handleTaskSubmit = async (prompt, maxRetries, networkPolicy) => {
    setIsSubmitting(true);
    setEvents([]);
    try {
      const res = await submitTask(prompt, maxRetries, networkPolicy);
      setCurrentTaskId(res.task_id);
    } catch (err) {
      alert("Task submission error: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelTask = async () => {
    if (!currentTaskId) return;
    try {
      await cancelTask(currentTaskId);
    } catch (err) {
      console.error("Cancel failed:", err);
    }
  };

  const currentState = taskData?.state || "RECEIVED";
  const currentAttempt = taskData?.current_attempt || 1;
  const maxRetries = taskData?.max_retries || 3;
  const isTerminal = ["COMPLETED", "FAILED", "CANCELLED"].includes(currentState);

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Navbar
        wsConnected={wsConnected}
        stats={stats}
        onToggleBenchmark={() => setShowBenchmark(!showBenchmark)}
        showBenchmark={showBenchmark}
      />

      <main style={{ flex: 1, padding: "28px 32px", maxWidth: "1600px", margin: "0 auto", width: "100%" }}>
        {showBenchmark ? (
          <BenchmarkPanel />
        ) : (
          <>
            {/* Task Submission Section */}
            <TaskInput onSubmit={handleTaskSubmit} isSubmitting={isSubmitting} />

            {/* State Machine Pipeline */}
            {currentTaskId && (
              <StatePipeline
                currentState={currentState}
                currentAttempt={currentAttempt}
                maxRetries={maxRetries}
                onCancel={handleCancelTask}
                isTerminal={isTerminal}
              />
            )}

            {/* Main Execution Workspace Grid */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
              gap: "24px",
              marginBottom: "24px"
            }}>
              {/* Left Column: Live Logs & Telemetry */}
              <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                <LiveLogs events={events} />
                <MetricsPanel metrics={{
                  duration_sec: taskData?.total_duration_sec,
                  cpu_pct: 0.4,
                  mem_mb: 45,
                  runner: "docker"
                }} />
              </div>

              {/* Right Column: Code Evolution & Diff */}
              <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                <CodeViewer
                  codeVersions={taskData?.code_versions || []}
                  latestCode={taskData?.latest_code}
                />
                <ValidationDeliverables
                  taskId={currentTaskId}
                  validation={{
                    passed: taskData?.validation_passed,
                    score: taskData?.validation_score,
                    is_false_success: !taskData?.validation_passed && taskData?.state === "COMPLETED",
                    checks: [
                      { name: "Deliverable Image Generated", passed: (taskData?.artifacts?.length || 0) > 0 },
                      { name: "Aggregations Validated", passed: taskData?.validation_passed || false }
                    ]
                  }}
                  artifacts={taskData?.artifacts || []}
                />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
