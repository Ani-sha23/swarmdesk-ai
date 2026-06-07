// frontend/components/TicketForm.tsx
"use client";
import { useState } from "react";
import { submitTicket } from "@/lib/api";

export default function TicketForm({ onResult, setLoading, loading }: any) {
  const [subject, setSubject] = useState("");
  const [body, setBody]       = useState("");

  async function handleSubmit() {
    if (!subject.trim() || !body.trim()) return;
    setLoading(true);
    onResult(null);
    try {
      const data = await submitTicket({ subject, body, user_id: "portal_user" });
      onResult(data);
    } catch (e) {
      alert("API error — make sure the backend is running on localhost:8000");
    } finally {
      setLoading(false);
    }
  }

  const examples = [
    "I was charged twice for Pro. Dashboard also shows inactive.",
    "My account was hacked — someone changed my payment without my authorization.",
    "Getting 429 rate limit errors on the API even on Pro plan.",
  ];

  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <h2 className="font-semibold text-gray-200 mb-4">Submit Support Ticket</h2>

      <div className="mb-3">
        <label className="text-xs text-gray-400 mb-1 block">SUBJECT</label>
        <input
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
          placeholder="Brief summary of your issue"
          value={subject}
          onChange={e => setSubject(e.target.value)}
        />
      </div>

      <div className="mb-4">
        <label className="text-xs text-gray-400 mb-1 block">DESCRIBE YOUR ISSUE</label>
        <textarea
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm h-28 resize-none focus:outline-none focus:border-cyan-500"
          placeholder="Describe your problem in detail..."
          value={body}
          onChange={e => setBody(e.target.value)}
        />
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        <span className="text-xs text-gray-500">Try:</span>
        {examples.map((ex, i) => (
          <button key={i}
            onClick={() => { setSubject(ex.split(".")[0]); setBody(ex); }}
            className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-2 py-1 rounded-md border border-gray-700"
          >
            Example {i + 1}
          </button>
        ))}
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading || !subject || !body}
        className="w-full bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 text-black font-semibold py-2 rounded-lg transition-colors"
      >
        {loading ? "Processing..." : "Submit to SwarmDesk AI →"}
      </button>
    </div>
  );
}
