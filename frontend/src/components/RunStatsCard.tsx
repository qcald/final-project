import { Cpu } from 'lucide-react'
import type { RunStats } from '../types'

export default function RunStatsCard({ run }: { run: RunStats | null }) {
  const stats: [string, string][] = run
    ? [
        ['Input tokens', run.input_tokens.toLocaleString()],
        ['Output tokens', run.output_tokens.toLocaleString()],
        ['Cached input', run.cached_input_tokens.toLocaleString()],
        ['Time', `${run.seconds.toFixed(1)}s`],
      ]
    : []

  return (
    <div className="card stats-card">
      <h3 className="card-title">
        <Cpu size={16} /> Last AI run
      </h3>
      {run ? (
        <>
          <div className="stats-grid">
            {stats.map(([label, value]) => (
              <div key={label} className="stat">
                <b>{value}</b>
                <span>{label}</span>
              </div>
            ))}
          </div>
          <p className="hint" style={{ margin: '10px 0 0' }}>
            {run.calls} model call{run.calls === 1 ? '' : 's'} ·{' '}
            {run.cost_usd === null ? 'set prices in config.py to see cost' : `$${run.cost_usd.toFixed(5)}`}
          </p>
        </>
      ) : (
        <p className="hint" style={{ margin: 0 }}>Token counts for your next question or import show up here.</p>
      )}
    </div>
  )
}
