import React from "react";

export default function Navbar({ wsConnected, stats, onToggleBenchmark, showBenchmark }) {
  return (
    <header style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "16px 32px",
      borderBottom: "1px solid var(--border-subtle)",
      background: "rgba(10, 13, 20, 0.8)",
      backdropFilter: "blur(12px)",
      position: "sticky",
      top: 0,
      zIndex: 50
    }}>
      {/* Brand & Title */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <div style={{
          width: "42px",
          height: "42px",
          borderRadius: "12px",
          background: "linear-gradient(135deg, #6366f1, #a855f7)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 4px 20px var(--primary-glow)",
          color: "#fff",
          fontWeight: "800",
          fontSize: "1.2rem",
          letterSpacing: "-0.03em"
        }}>
          R
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.35rem", fontWeight: "800", letterSpacing: "-0.02em", color: "#f8fafc" }}>
              ReRun
            </h1>
            <span style={{
              fontSize: "0.7rem",
              fontWeight: "700",
              background: "rgba(99, 102, 241, 0.2)",
              color: "#a5b4fc",
              padding: "2px 8px",
              borderRadius: "6px",
              border: "1px solid rgba(99, 102, 241, 0.3)"
            }}>
              RESEARCH PROTOTYPE
            </span>
          </div>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Hierarchical Autonomous Coding Agent with Runtime-Guided Recovery & Sandboxed Execution
          </p>
        </div>
      </div>

      {/* Stats & Connection Indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
        {stats && (
          <div style={{ display: "flex", gap: "18px", fontSize: "0.82rem" }}>
            <div style={{ textAlign: "right" }}>
              <span style={{ color: "var(--text-faint)", display: "block", fontSize: "0.72rem" }}>COMPLETED</span>
              <strong style={{ color: "var(--accent-emerald)" }}>{stats.completed_tasks} / {stats.total_tasks}</strong>
            </div>
            <div style={{ textAlign: "right" }}>
              <span style={{ color: "var(--text-faint)", display: "block", fontSize: "0.72rem" }}>SUCCESS RATE</span>
              <strong style={{ color: "#a5b4fc" }}>{(stats.success_rate * 100).toFixed(0)}%</strong>
            </div>
          </div>
        )}

        <button
          onClick={onToggleBenchmark}
          style={{
            background: showBenchmark ? "var(--primary)" : "rgba(255, 255, 255, 0.05)",
            border: "1px solid var(--border-subtle)",
            color: "#fff",
            padding: "8px 16px",
            borderRadius: "var(--radius-md)",
            fontSize: "0.85rem",
            fontWeight: "600",
            cursor: "pointer",
            transition: "all 0.2s"
          }}
        >
          {showBenchmark ? "← Task Workspace" : "📊 Benchmark & Baselines"}
        </button>

        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          background: wsConnected ? "rgba(16, 185, 129, 0.12)" : "rgba(244, 63, 94, 0.12)",
          padding: "6px 12px",
          borderRadius: "9999px",
          border: `1px solid ${wsConnected ? "rgba(16, 185, 129, 0.25)" : "rgba(244, 63, 94, 0.25)"}`
        }}>
          <span style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            backgroundColor: wsConnected ? "#10b981" : "#f43f5e",
            boxShadow: wsConnected ? "0 0 8px #10b981" : "0 0 8px #f43f5e"
          }} />
          <span style={{
            fontSize: "0.75rem",
            fontWeight: "600",
            color: wsConnected ? "#34d399" : "#fb7185"
          }}>
            {wsConnected ? "LIVE STREAM" : "OFFLINE"}
          </span>
        </div>
      </div>
    </header>
  );
}
