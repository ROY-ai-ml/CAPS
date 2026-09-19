import React from "react";
import { getArtifactUrl } from "../services/api";

export default function ValidationDeliverables({ taskId, validation, artifacts = [] }) {
  const isFalseSuccess = validation?.is_false_success;
  const isPassed = validation?.passed;

  return (
    <div className="glass-panel" style={{ padding: "20px 24px", height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h3 style={{ fontSize: "1.05rem", fontWeight: "700" }}>Task Validation & Deliverables</h3>
        {validation && (
          <span style={{
            fontSize: "0.85rem",
            fontWeight: "700",
            color: isPassed ? "#34d399" : isFalseSuccess ? "#fbbf24" : "#fb7185",
            background: isPassed ? "rgba(16, 185, 129, 0.15)" : isFalseSuccess ? "rgba(245, 158, 11, 0.15)" : "rgba(244, 63, 94, 0.15)",
            padding: "4px 12px",
            borderRadius: "9999px",
            border: `1px solid ${isPassed ? "#10b981" : isFalseSuccess ? "#f59e0b" : "#f43f5e"}`
          }}>
            {isPassed ? "✓ VALIDATION PASSED" : isFalseSuccess ? "⚠️ FALSE SUCCESS DETECTED" : "✗ VALIDATION FAILED"}
          </span>
        )}
      </div>

      {/* False Success Alert Banner */}
      {isFalseSuccess && (
        <div style={{
          background: "rgba(245, 158, 11, 0.12)",
          border: "1px solid rgba(245, 158, 11, 0.35)",
          borderRadius: "var(--radius-md)",
          padding: "12px 16px",
          marginBottom: "16px",
          color: "#fde68a",
          fontSize: "0.84rem",
          lineHeight: "1.5"
        }}>
          <div style={{ fontWeight: "700", marginBottom: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
            <span>⚠️</span> Execution Success ≠ Task Success
          </div>
          <div>{validation.explanation}</div>
        </div>
      )}

      {/* Validation Checks */}
      {validation?.checks && validation.checks.length > 0 && (
        <div style={{ marginBottom: "20px" }}>
          <span style={{ fontSize: "0.76rem", color: "var(--text-muted)", fontWeight: "600", textTransform: "uppercase" }}>
            Verification Checks
          </span>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "8px" }}>
            {validation.checks.map((chk, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "6px 12px",
                  background: "rgba(255, 255, 255, 0.02)",
                  borderRadius: "6px",
                  fontSize: "0.8rem",
                }}
              >
                <span style={{ color: "var(--text-main)" }}>{chk.name}</span>
                <span style={{ color: chk.passed ? "#34d399" : "#fb7185", fontWeight: "600" }}>
                  {chk.passed ? "PASSED" : "FAILED"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generated Artifacts Showcase */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <span style={{ fontSize: "0.76rem", color: "var(--text-muted)", fontWeight: "600", textTransform: "uppercase", marginBottom: "10px" }}>
          Captured Artifacts ({artifacts.length})
        </span>

        {artifacts.length === 0 ? (
          <div style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(0, 0, 0, 0.2)",
            borderRadius: "var(--radius-md)",
            color: "var(--text-faint)",
            fontSize: "0.85rem",
            minHeight: "140px"
          }}>
            No artifacts generated for this attempt yet.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {artifacts.map((art, idx) => {
              const isImage = art.filename.endsWith(".png") || art.filename.endsWith(".jpg") || art.filename.endsWith(".svg");
              const url = getArtifactUrl(taskId, art.filename);

              return (
                <div
                  key={idx}
                  style={{
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "10px"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontSize: "1.1rem" }}>{isImage ? "🖼️" : "📄"}</span>
                      <div>
                        <strong style={{ fontSize: "0.85rem", color: "#f8fafc", display: "block" }}>{art.filename}</strong>
                        <span style={{ fontSize: "0.72rem", color: "var(--text-faint)" }}>
                          {(art.file_size_bytes / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    </div>
                    <a
                      href={url}
                      download={art.filename}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        background: "rgba(99, 102, 241, 0.2)",
                        border: "1px solid rgba(99, 102, 241, 0.4)",
                        color: "#a5b4fc",
                        padding: "5px 12px",
                        borderRadius: "6px",
                        fontSize: "0.75rem",
                        textDecoration: "none",
                        fontWeight: "600"
                      }}
                    >
                      Download
                    </a>
                  </div>

                  {/* Render Image Preview */}
                  {isImage && (
                    <div style={{
                      borderRadius: "var(--radius-sm)",
                      overflow: "hidden",
                      border: "1px solid rgba(255, 255, 255, 0.08)",
                      background: "#0d1117",
                      textAlign: "center"
                    }}>
                      <img
                        src={url}
                        alt={art.filename}
                        style={{
                          maxWidth: "100%",
                          maxHeight: "220px",
                          objectFit: "contain",
                          display: "block",
                          margin: "0 auto"
                        }}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
