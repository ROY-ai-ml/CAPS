import React, { useState } from "react";

const PRESETS = [
  {
    title: "📊 CSV Analysis & Chart",
    desc: "Happy Path",
    prompt: "Analyze sales.csv, calculate monthly revenue, and generate sales_chart.png",
  },
  {
    title: "🔧 KeyError Diagnosis & Recovery",
    desc: "Self-Repair Demo",
    prompt: "Analyze sales.csv, calculate monthly revenue, and generate sales_chart.png (inject_key_error)",
  },
  {
    title: "⚠️ False-Success Detection",
    desc: "Exit Code 0 != Success",
    prompt: "Analyze sales data and generate sales_chart.png (inject_false_success)",
  },
  {
    title: "🛡️ Hard Security Block",
    desc: "Hostile Code Rejection",
    prompt: "Execute system scan using subprocess and shell commands",
  },
  {
    title: "⏱️ Timeout Recovery",
    desc: "Optimization Demo",
    prompt: "Process dataset with high latency simulation (inject_timeout)",
  },
];

export default function TaskInput({ onSubmit, isSubmitting }) {
  const [prompt, setPrompt] = useState(PRESETS[0].prompt);
  const [maxRetries, setMaxRetries] = useState(3);
  const [networkPolicy, setNetworkPolicy] = useState("DISABLED");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim() || isSubmitting) return;
    onSubmit(prompt, maxRetries, networkPolicy);
  };

  return (
    <div className="glass-panel" style={{ padding: "24px", marginBottom: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: "700", color: "var(--text-main)" }}>
          Submit Autonomous Task
        </h2>
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          Master Agent will plan, generate, sandbox, observe, and verify.
        </span>
      </div>

      {/* Preset Pills */}
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "16px" }}>
        {PRESETS.map((p, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setPrompt(p.prompt)}
            style={{
              background: prompt === p.prompt ? "rgba(99, 102, 241, 0.25)" : "rgba(255, 255, 255, 0.04)",
              border: `1px solid ${prompt === p.prompt ? "var(--primary)" : "var(--border-subtle)"}`,
              borderRadius: "var(--radius-md)",
              padding: "8px 12px",
              cursor: "pointer",
              textAlign: "left",
              transition: "all 0.2s",
            }}
          >
            <div style={{ fontSize: "0.82rem", fontWeight: "600", color: "#f8fafc" }}>{p.title}</div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-faint)" }}>{p.desc}</div>
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "16px" }}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
            placeholder="Describe the task in natural language (e.g. Read CSV, calculate monthly aggregates, and plot a chart)..."
            style={{
              width: "100%",
              padding: "14px 16px",
              background: "rgba(11, 15, 25, 0.8)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              color: "#fff",
              fontFamily: "var(--font-sans)",
              fontSize: "0.95rem",
              resize: "vertical",
              outline: "none",
            }}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
            {/* Max Retries */}
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <label style={{ fontSize: "0.82rem", color: "var(--text-muted)", fontWeight: "500" }}>
                Max Retries:
              </label>
              <select
                value={maxRetries}
                onChange={(e) => setMaxRetries(Number(e.target.value))}
                style={{
                  background: "rgba(15, 23, 42, 0.8)",
                  border: "1px solid var(--border-subtle)",
                  color: "#fff",
                  padding: "6px 10px",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.85rem",
                }}
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{n} attempts</option>
                ))}
              </select>
            </div>

            {/* Network Policy */}
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <label style={{ fontSize: "0.82rem", color: "var(--text-muted)", fontWeight: "500" }}>
                Network Egress:
              </label>
              <select
                value={networkPolicy}
                onChange={(e) => setNetworkPolicy(e.target.value)}
                style={{
                  background: "rgba(15, 23, 42, 0.8)",
                  border: "1px solid var(--border-subtle)",
                  color: "#fff",
                  padding: "6px 10px",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.85rem",
                }}
              >
                <option value="DISABLED">DISABLED (Isolated --network none)</option>
                <option value="ALLOWLIST">ALLOWLIST (Approved domains only)</option>
                <option value="CONTROLLED">CONTROLLED (Full monitored egress)</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !prompt.trim()}
            style={{
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              color: "#fff",
              border: "none",
              padding: "10px 24px",
              borderRadius: "var(--radius-md)",
              fontWeight: "700",
              fontSize: "0.95rem",
              cursor: isSubmitting ? "not-allowed" : "pointer",
              boxShadow: "0 4px 18px var(--primary-glow)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              opacity: isSubmitting ? 0.7 : 1,
            }}
          >
            {isSubmitting ? (
              <>
                <span className="spin">⚡</span> Starting Agent...
              </>
            ) : (
              <>
                <span>🚀</span> Dispatch to Master Agent
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
