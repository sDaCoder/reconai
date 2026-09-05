const RECONCILIATION_API_URL = "http://localhost:8000/reconciliation-cases";
const RECONCILE_STREAM_API_URL = "http://localhost:8000/reconcile/stream";

export async function getReconciliationCases() {
  const res = await fetch(RECONCILIATION_API_URL, { cache: "no-store" });
  return res.json();
}

export async function reconcileQueryStream(query, onToken) {
  const res = await fetch(RECONCILE_STREAM_API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok || !res.body) throw new Error("Reconcile request failed");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let separatorIndex;
    while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);

      const token = rawEvent
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).replace(/^ /, ""))
        .join("\n");
      if (token) onToken(token);
    }
  }
}

export function classifyStatus(status) {
  const s = status.toLowerCase();
  if (s === "matched" || s === "reconciled") return "reconciled";
  if (s === "adjusted" || s === "resolved_discrepancy") return "explained";
  return "exception";
}

export function formatStatusLabel(status) {
  return status
    .toLowerCase()
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export function formatCaseCode(caseId) {
  return `RC-${String(caseId).padStart(3, "0")}`;
}
