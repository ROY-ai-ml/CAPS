import React, { useState } from "react";

export default function CodeViewer({ codeVersions = [], latestCode }) {
  const [selectedVersionIdx, setSelectedVersionIdx] = useState(
    codeVersions.length > 0 ? codeVersions.length - 1 : 0
  );
  const [viewMode, setViewMode] = useState("diff"); // "code" or "diff"
  const [copied, setCopied] = useState(false);

  // Sync selected index if new versions arrive
  React.useEffect(() => {
    if (codeVersions.length > 0) {
      setSelectedVersionIdx(codeVersions.length - 1);
    }
  }, [codeVersions.length]);

  const currentVer = codeVersions[selectedVersionIdx];
  const codeToDisplay = currentVer ? currentVer.source_code || latestCode : latestCode || "# No code generated yet.";
  const diffToDisplay = currentVer ? currentVer.diff_from_parent : null;

  const handleCopy = () => {
    navigator.clipboard.writeText(codeToDisplay);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderDiffLines = (diffText) => {
    if (!diffText) {
      return (
        <div style={{ color: "var(--text-faint)", padding: "20px", textAlign: "center" }}>
          Initial code version (No parent diff available).
        </div>
      );
    }

    return diffText.split("\n").map((line, i) => {
      let bg = "transparent";
      let color = "var(--text-main)";

      if (line.startsWith("+") && !line.startsWith("+++")) {
        bg = "rgba(16, 185, 129, 0.15)";
        color = "#34d399";
      } else if (line.startsWith("-") && !line.startsWith("---")) {
        bg = "rgba(244, 63, 94, 0.15)";
        color = "#fb7185";
      } else if (line.startsWith("@")) {
        color = "#818cf8";
      }

      return (
        <div
          key={i}
          style={{
            background: bg,
            color: color,
            padding: "2px 8px",
            whiteSpace: "pre-wrap",
            wordBreak: "break-all",
          }}
        >
          {line}
        </div>
      );
    });
  };

  return (
    <div className="glass-panel" style={{ display: "flex", flexDirection: "column", height: "420px" }}>
      {/* Header with Version Tabs */}
      <div style={{
        padding: "12px 18px",
        borderBottom: "1px solid var(--border-subtle)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "10px"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "0.95rem", fontWeight: "700" }}>Code Evolution</span>
          {codeVersions.map((cv, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedVersionIdx(idx)}
              style={{
                background: selectedVersionIdx === idx ? "var(--primary)" : "rgba(255, 255, 255, 0.05)",
                color: "#fff",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                padding: "4px 10px",
                fontSize: "0.75rem",
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              {cv.version_tag || `Attempt ${cv.version}`}
            </button>
          ))}
        </div>

        {/* View Toggle & Copy */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          {diffToDisplay && (
            <div style={{ display: "flex", background: "rgba(0,0,0,0.3)", borderRadius: "6px", padding: "2px" }}>
              <button
                onClick={() => setViewMode("diff")}
                style={{
                  background: viewMode === "diff" ? "rgba(99, 102, 241, 0.3)" : "transparent",
                  border: "none",
                  color: "#fff",
                  padding: "4px 10px",
                  borderRadius: "4px",
                  fontSize: "0.72rem",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Diff
              </button>
              <button
                onClick={() => setViewMode("code")}
                style={{
                  background: viewMode === "code" ? "rgba(99, 102, 241, 0.3)" : "transparent",
                  border: "none",
                  color: "#fff",
                  padding: "4px 10px",
                  borderRadius: "4px",
                  fontSize: "0.72rem",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Code
              </button>
            </div>
          )}

          <button
            onClick={handleCopy}
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-muted)",
              padding: "4px 10px",
              borderRadius: "6px",
              fontSize: "0.75rem",
              cursor: "pointer",
            }}
          >
            {copied ? "✓ Copied" : "📋 Copy"}
          </button>
        </div>
      </div>

      {/* Modification Reason Bar */}
      {currentVer?.modification_reason && (
        <div style={{
          padding: "6px 18px",
          background: "rgba(99, 102, 241, 0.08)",
          borderBottom: "1px solid var(--border-subtle)",
          fontSize: "0.76rem",
          color: "#a5b4fc",
          display: "flex",
          alignItems: "center",
          gap: "6px"
        }}>
          <span>💡</span>
          <strong>Intent:</strong> {currentVer.modification_reason}
        </div>
      )}

      {/* Code / Diff Body */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "14px 18px",
        fontFamily: "var(--font-mono)",
        fontSize: "0.82rem",
        lineHeight: "1.6",
        background: "rgba(5, 7, 12, 0.6)"
      }}>
        {viewMode === "diff" && diffToDisplay ? (
          renderDiffLines(diffToDisplay)
        ) : (
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{codeToDisplay}</pre>
        )}
      </div>
    </div>
  );
}
