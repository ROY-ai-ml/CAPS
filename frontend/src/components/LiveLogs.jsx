import React, { useEffect, useRef } from "react";

export default function LiveLogs({ events }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  const formatTime = (ts) => {
    if (!ts) return "";
    const date = new Date(ts);
    return date.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
  };

  const getEventBadgeColor = (type) => {
    if (type.includes("failed") || type.includes("violation")) return "#f43f5e";
    if (type.includes("completed") || type.includes("passed")) return "#10b981";
    if (type.includes("recovery") || type.includes("repair")) return "#f59e0b";
    if (type.includes("sandbox") || type.includes("exec")) return "#06b6d4";
    return "#818cf8";
  };

  return (
    <div className="glass-panel" style={{ display: "flex", flexDirection: "column", height: "380px" }}>
      <div style={{
        padding: "14px 20px",
        borderBottom: "1px solid var(--border-subtle)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "0.95rem", fontWeight: "700" }}>Live Execution Trace</span>
          <span style={{
            fontSize: "0.72rem",
            background: "rgba(255, 255, 255, 0.08)",
            padding: "2px 8px",
            borderRadius: "10px",
            color: "var(--text-muted)"
          }}>
            {events.length} events
          </span>
        </div>
      </div>

      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "12px 18px",
          fontFamily: "var(--font-mono)",
          fontSize: "0.8rem",
          display: "flex",
          flexDirection: "column",
          gap: "8px"
        }}
      >
        {events.length === 0 ? (
          <div style={{ color: "var(--text-faint)", textAlign: "center", padding: "40px 0" }}>
            Awaiting task execution events...
          </div>
        ) : (
          events.map((evt, idx) => {
            const time = formatTime(evt.timestamp);
            const color = getEventBadgeColor(evt.type || evt.event_type || "");
            const agent = evt.agent || evt.agent_name || "system";
            const details = evt.details || {};

            return (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "12px",
                  padding: "6px 8px",
                  borderRadius: "var(--radius-sm)",
                  background: idx % 2 === 0 ? "rgba(255, 255, 255, 0.015)" : "transparent",
                }}
              >
                <span style={{ color: "var(--text-faint)", flexShrink: 0, fontSize: "0.75rem" }}>
                  {time}
                </span>

                <span style={{
                  padding: "1px 6px",
                  borderRadius: "4px",
                  fontSize: "0.68rem",
                  fontWeight: "700",
                  textTransform: "uppercase",
                  color: color,
                  border: `1px solid ${color}40`,
                  background: `${color}15`,
                  flexShrink: 0
                }}>
                  {evt.type || evt.event_type}
                </span>

                <div style={{ flex: 1, color: "var(--text-main)" }}>
                  <span style={{ color: "var(--text-muted)", marginRight: "6px" }}>[{agent}]</span>
                  {details.message || details.reason || details.error_message || (
                    details.error_type ? `${details.error_type}: ${details.error_message || ''}` : JSON.stringify(details)
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
