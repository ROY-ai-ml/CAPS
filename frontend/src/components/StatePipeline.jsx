import React from "react";

const STAGES = [
  { id: "MASTER", label: "Master Agent", states: ["RECEIVED"] },
  { id: "PLANNER", label: "Planner", states: ["PLANNING", "PLAN_READY", "REPLANNING"] },
  { id: "CODING", label: "Coding Agent", states: ["GENERATING", "RETRYING"] },
  { id: "SECURITY", label: "Security Policy", states: ["SECURITY_CHECK", "BLOCKED"] },
  { id: "SANDBOX", label: "Docker Sandbox", states: ["EXECUTING", "TIMEOUT"] },
  { id: "OBSERVER", label: "Observer", states: ["OBSERVING"] },
  { id: "RECOVERY", label: "Debug/Recovery", states: ["ANALYZING_FAILURE", "REPAIRING"] },
  { id: "VALIDATOR", label: "Task Validator", states: ["VALIDATING", "COMPLETED", "FAILED"] },
];

export default function StatePipeline({ currentState, currentAttempt, maxRetries, onCancel, isTerminal }) {
  const getStageStatus = (stage) => {
    if (stage.states.includes(currentState)) return "active";
    // Check if stage was passed
    const activeStageIndex = STAGES.findIndex(s => s.states.includes(currentState));
    const thisIndex = STAGES.findIndex(s => s.id === stage.id);
    if (activeStageIndex > thisIndex) return "completed";
    return "pending";
  };

  const getStateColor = (state) => {
    switch (state) {
      case "COMPLETED": return "#10b981";
      case "FAILED":
      case "BLOCKED": return "#f43f5e";
      case "TIMEOUT":
      case "ANALYZING_FAILURE":
      case "REPAIRING": return "#f59e0b";
      case "EXECUTING": return "#06b6d4";
      default: return "#6366f1";
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "20px 24px", marginBottom: "24px" }}>
      {/* Top Header: Current State & Human Override */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontWeight: "600" }}>CURRENT STAGE:</span>
          <span
            className={`badge badge-${currentState.toLowerCase()}`}
            style={{
              fontSize: "0.85rem",
              padding: "6px 14px",
              background: `rgba(99, 102, 241, 0.15)`,
              color: getStateColor(currentState),
              borderColor: getStateColor(currentState),
            }}
          >
            ● {currentState}
          </span>
          <span style={{ fontSize: "0.82rem", color: "var(--text-faint)" }}>
            (Attempt {currentAttempt} of {maxRetries})
          </span>
        </div>

        {!isTerminal && (
          <button
            onClick={onCancel}
            style={{
              background: "rgba(244, 63, 94, 0.12)",
              border: "1px solid rgba(244, 63, 94, 0.3)",
              color: "#fb7185",
              padding: "6px 16px",
              borderRadius: "var(--radius-md)",
              fontSize: "0.82rem",
              fontWeight: "600",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            ⏹ Cancel Task
          </button>
        )}
      </div>

      {/* Pipeline Stage Nodes */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "relative",
        overflowX: "auto",
        padding: "10px 0"
      }}>
        {STAGES.map((stage, i) => {
          const status = getStageStatus(stage);
          const isActive = status === "active";
          const isDone = status === "completed";

          return (
            <React.Fragment key={stage.id}>
              <div style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                zIndex: 2,
                minWidth: "90px"
              }}>
                <div style={{
                  width: "40px",
                  height: "40px",
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.85rem",
                  fontWeight: "700",
                  background: isActive
                    ? "linear-gradient(135deg, #6366f1, #06b6d4)"
                    : isDone
                    ? "rgba(16, 185, 129, 0.2)"
                    : "rgba(255, 255, 255, 0.05)",
                  color: isActive ? "#fff" : isDone ? "#34d399" : "var(--text-faint)",
                  border: `2px solid ${
                    isActive ? "#22d3ee" : isDone ? "#10b981" : "rgba(255, 255, 255, 0.1)"
                  }`,
                  boxShadow: isActive ? "0 0 16px rgba(6, 182, 212, 0.6)" : "none",
                  transition: "all 0.3s ease",
                }}>
                  {isDone ? "✓" : i + 1}
                </div>
                <span style={{
                  marginTop: "8px",
                  fontSize: "0.74rem",
                  fontWeight: isActive ? "700" : "500",
                  color: isActive ? "#f8fafc" : isDone ? "#cbd5e1" : "var(--text-faint)",
                  textAlign: "center",
                }}>
                  {stage.label}
                </span>
              </div>

              {i < STAGES.length - 1 && (
                <div style={{
                  flex: 1,
                  height: "2px",
                  background: isDone
                    ? "linear-gradient(90deg, #10b981, #6366f1)"
                    : isActive
                    ? "linear-gradient(90deg, #6366f1, rgba(255,255,255,0.1))"
                    : "rgba(255, 255, 255, 0.08)",
                  minWidth: "20px",
                  margin: "0 4px",
                  position: "relative",
                  top: "-12px",
                  transition: "background 0.3s ease",
                }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
