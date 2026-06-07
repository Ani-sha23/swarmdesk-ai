// frontend/components/ResponseCard.tsx
export default function ResponseCard({ result }: any) {
  const { response, escalated, confidence, verdict, total_duration_ms } = result;

  return (
    <div className={`rounded-2xl p-6 border ${escalated ? "border-red-500 bg-red-950/30" : "border-green-500 bg-green-950/20"}`}>
      <div className="flex items-center gap-3 mb-4">
        <span className={`text-2xl font-bold ${escalated ? "text-red-400" : "text-green-400"}`}>
          {escalated ? "⚠️ Escalated to Human Agent" : "✅ Resolved by Swarm"}
        </span>
        <span className="ml-auto text-xs text-gray-400">{total_duration_ms}ms</span>
      </div>

      <div className="flex gap-4 mb-4">
        <div className="bg-gray-800 rounded-lg px-4 py-2 text-center">
          <div className={`text-2xl font-bold ${confidence >= 75 ? "text-green-400" : "text-red-400"}`}>
            {confidence}<span className="text-sm text-gray-400">/100</span>
          </div>
          <div className="text-xs text-gray-400">Confidence</div>
        </div>
        <div className="bg-gray-800 rounded-lg px-4 py-2 text-center">
          <div className={`text-xl font-bold ${verdict === "PASS" ? "text-green-400" : "text-red-400"}`}>{verdict}</div>
          <div className="text-xs text-gray-400">Verdict</div>
        </div>
      </div>

      {response ? (
        <div className="bg-gray-800 rounded-lg p-4 text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">
          {response}
        </div>
      ) : (
        <div className="text-sm text-red-300">
          This ticket has been escalated to a human agent with full context.
          You will receive a follow-up within the SLA window.
        </div>
      )}
    </div>
  );
}
