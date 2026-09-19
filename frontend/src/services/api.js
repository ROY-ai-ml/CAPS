/** API Service for ReRun Backend */
const isBrowser = typeof window !== "undefined";
const host = isBrowser && window.location.host ? window.location.host : "localhost:8000";
const protocol = isBrowser && window.location.protocol === "https:" ? "https:" : "http:";
const wsProtocol = isBrowser && window.location.protocol === "https:" ? "wss:" : "ws:";

const API_BASE = `${protocol}//${host}/api`;
export const WS_BASE = `${wsProtocol}//${host}/api/ws`;

export async function submitTask(prompt, maxRetries = 3, networkPolicy = "DISABLED") {
  const resp = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      max_retries: maxRetries,
      network_policy: networkPolicy,
    }),
  });
  if (!resp.ok) throw new Error("Failed to submit task");
  return resp.json();
}

export async function fetchTask(taskId) {
  const resp = await fetch(`${API_BASE}/tasks/${taskId}`);
  if (!resp.ok) throw new Error("Failed to fetch task");
  return resp.json();
}

export async function fetchTasks() {
  const resp = await fetch(`${API_BASE}/tasks`);
  if (!resp.ok) throw new Error("Failed to list tasks");
  return resp.json();
}

export async function cancelTask(taskId) {
  const resp = await fetch(`${API_BASE}/tasks/${taskId}/cancel`, {
    method: "POST",
  });
  if (!resp.ok) throw new Error("Failed to cancel task");
  return resp.json();
}

export async function fetchTaskEvents(taskId) {
  const resp = await fetch(`${API_BASE}/tasks/${taskId}/events`);
  if (!resp.ok) throw new Error("Failed to fetch events");
  return resp.json();
}

export function getArtifactUrl(taskId, filename) {
  return `${API_BASE}/artifacts/${taskId}/${filename}`;
}
