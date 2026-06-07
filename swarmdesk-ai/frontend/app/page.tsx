// frontend/app/page.tsx — SwarmDesk AI Portal
"use client";
import { useState } from "react";
import TicketForm from "@/components/TicketForm";
import AgentTrace from "@/components/AgentTrace";
import ResponseCard from "@/components/ResponseCard";

export default function Home() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-8 py-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-cyan-500 flex items-center justify-center font-bold text-black text-sm">S</div>
        <span className="font-semibold text-lg">SwarmDesk AI</span>
        <span className="ml-auto text-xs text-gray-500">Microsoft Build AI Hackathon 2026 · Team InnovaLite</span>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-10 grid grid-cols-1 gap-8">
        <div>
          <h1 className="text-3xl font-bold mb-1">Multi-Agent Support Portal</h1>
          <p className="text-gray-400 text-sm">5 AI agents collaborate in real time to resolve your ticket</p>
        </div>

        {/* Ticket Form */}
        <TicketForm onResult={setResult} setLoading={setLoading} loading={loading} />

        {/* Results */}
        {loading && (
          <div className="text-center py-12">
            <div className="animate-pulse text-cyan-400 text-lg font-mono">
              ⚡ Agent swarm processing...
            </div>
            <p className="text-gray-500 text-sm mt-2">Planner → Retriever → Responder → Validator</p>
          </div>
        )}

        {result && !loading && (
          <div className="grid grid-cols-1 gap-6">
            <ResponseCard result={result} />
            <AgentTrace traces={result.agent_traces} duration={result.total_duration_ms} />
          </div>
        )}
      </div>
    </main>
  );
}
