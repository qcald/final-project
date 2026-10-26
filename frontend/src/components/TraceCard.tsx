import { ChevronDown, CircleCheck, MapPin, ShieldCheck, Sparkles, Workflow, type LucideIcon } from 'lucide-react'
import type { TraceStep } from '../types'

const KIND: Record<TraceStep['kind'], { Icon: LucideIcon; label: string }> = {
  check: { Icon: ShieldCheck, label: 'Safety check' },
  tool: { Icon: MapPin, label: 'Tool' },
  model: { Icon: Sparkles, label: 'AI model' },
  result: { Icon: CircleCheck, label: 'Result' },
}

const AGENT_NAME: Record<string, string> = { intake: 'Intake agent', answer: 'Answer agent', resolver: 'Resolver' }

/** Step-by-step record of one run: every safety check, model call, and tool call, in order. */
export default function TraceCard({ trace, title = 'How this was made' }: { trace: TraceStep[]; title?: string }) {
  if (trace.length === 0) return null
  return (
    <details className="card trace-card">
      <summary>
        <h3 className="card-title">
          <Workflow size={16} /> {title}
          <span className="section-count">{trace.length} steps</span>
        </h3>
        <ChevronDown size={18} className="chev" />
      </summary>
      <ol className="trace">
        {trace.map((step, i) => {
          const { Icon, label } = KIND[step.kind] ?? KIND.check
          return (
            <li key={i} className={`trace-step kind-${step.kind}`}>
              <span className="trace-icon"><Icon size={14} /></span>
              <div className="trace-body">
                <div className="trace-head">
                  <b>{step.title}</b>
                  <span className="trace-meta">{AGENT_NAME[step.agent] ?? step.agent} · {label}</span>
                  <span className="trace-time">{(step.at_ms / 1000).toFixed(2)}s</span>
                </div>
                {step.detail && <div className="trace-detail">{step.detail}</div>}
              </div>
            </li>
          )
        })}
      </ol>
    </details>
  )
}
