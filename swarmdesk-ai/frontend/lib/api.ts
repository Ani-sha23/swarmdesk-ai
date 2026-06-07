// frontend/lib/api.ts — SwarmDesk API client
const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function submitTicket(payload: {
  user_id: string;
  subject: string;
  body: string;
  priority?: string;
}) {
  const resp = await fetch(`${BASE}/api/tickets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) throw new Error(`API error ${resp.status}`);
  return resp.json();
}

export async function getHealth() {
  const resp = await fetch(`${BASE}/health`);
  return resp.json();
}
