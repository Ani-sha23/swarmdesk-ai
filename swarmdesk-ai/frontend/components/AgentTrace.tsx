// frontend/components/AgentTrace.tsx
const AGENT_COLORS: Record<string, string> = {
  PlannerAgent:    "text-blue-400",
  RetrieverAgent:  "text-cyan-400",
  ResponderAgent:  "text-yellow-400",
  ValidatorAgent:  "text-purple-400",
  EscalationAgent: "text-red-400",
};

export default function AgentTrace({ traces, duration }: any) {
  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-200 font-mono text-sm">AGENT TRACE LOG</h3>
        <span className="text-xs text-gray-500">Total: {duration}ms</span>
      </div>
      <div className="space-y-2 font-mono text-xs">
        {traces.map((t: any, i: number) => (
          <div key={i} className="flex gap-3 bg-gray-800 rounded-lg px-3 py-2">
            <span className={`shrink-0 ${AGENT_COLORS[t.agent] || "text-gray-400"}`}>
              [{t.agent}]
            </span>
            <span className="text-gray-300 flex-1">{t.output}</span>
            <span className="text-gray-500 shrink-0">{t.duration_ms}ms</span>
          </div>
        ))}
      </div>
    </div>
  );
}
