import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, ShieldAlert, Clock, Cpu, Zap } from 'lucide-react'
import type { AdviseResult } from '../api'

const VERDICT_CONFIG = {
  recommend: { Icon: CheckCircle2, label: 'Recommended', sub: 'Safe to eat for your conditions' },
  limit: { Icon: AlertTriangle, label: 'Limit Intake', sub: 'Consume in moderation' },
  avoid: { Icon: XCircle, label: 'Avoid', sub: 'Not suitable for your conditions' },
  unknown: { Icon: HelpCircle, label: 'Unknown', sub: 'Insufficient data to assess' },
  uncertain: { Icon: HelpCircle, label: 'Uncertain', sub: 'AI could not determine suitability' },
}

const COND_CHIP: Record<string, string> = {
  recommend: 'chip-green',
  limit: 'chip-amber',
  avoid: 'chip-red',
  unknown: 'chip-gray',
}

interface Props {
  result: AdviseResult
  food: string
}

export default function VerdictCard({ result, food }: Props) {
  const v = (result.verdict?.toLowerCase() || 'unknown') as keyof typeof VERDICT_CONFIG
  const cfg = VERDICT_CONFIG[v] || VERDICT_CONFIG.unknown
  const { Icon } = cfg

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon blue">
          <Zap size={18} />
        </div>
        <div>
          <p className="card-title">Dietary Assessment</p>
          <p className="card-subtitle">{food.replace(/_/g, ' ')}</p>
        </div>
      </div>
      <div className="card-body">

        {/* Verdict banner */}
        <div className={`verdict-banner ${['recommend','limit','avoid'].includes(v) ? v : 'unknown'}`}>
          <div className="verdict-icon-wrap">
            <Icon size={24} />
          </div>
          <div>
            <p className="verdict-label">{cfg.label}</p>
            <p className="verdict-sublabel">{cfg.sub}</p>
          </div>
        </div>

        {/* Allergy alert */}
        {result.allergy_flag && (
          <div className="error-box" style={{ marginBottom: 16 }}>
            <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>Allergy alert — this food may contain an allergen you are sensitive to.</span>
          </div>
        )}

        {/* Reasoning */}
        {result.reason && (
          <div style={{ marginBottom: 20 }}>
            <p className="section-heading">Clinical Reasoning</p>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{result.reason}</p>
          </div>
        )}

        {/* Per-condition breakdown */}
        {result.per_condition && Object.keys(result.per_condition).length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <p className="section-heading">Per Condition</p>
            {Object.entries(result.per_condition).map(([cond, verd]) => {
              const cv = (verd?.toLowerCase() || 'unknown') as string
              return (
                <div key={cond} className="breakdown-row">
                  <span className="cond">{cond}</span>
                  <span className={`chip ${COND_CHIP[cv] || 'chip-gray'}`}>{cv}</span>
                </div>
              )
            })}
          </div>
        )}

        {/* Meta info grid */}
        <div className="info-grid">
          <div className="info-cell">
            <p className="info-label">Confidence</p>
            <p className="info-value" style={{ textTransform: 'capitalize' }}>{result.confidence}</p>
          </div>
          <div className="info-cell">
            <p className="info-label">Matrix Verdict</p>
            <p className="info-value" style={{ textTransform: 'capitalize' }}>{result.matrix_verdict}</p>
          </div>
          <div className="info-cell accent">
            <div style={{ display:'flex', alignItems:'center', gap:5 }}>
              <Clock size={10} style={{ color: '#93C5FD' }} />
              <p className="info-label" style={{ marginBottom:0 }}>Latency</p>
            </div>
            <p className="info-value">{result.latency_ms} ms</p>
          </div>
          <div className="info-cell accent">
            <div style={{ display:'flex', alignItems:'center', gap:5 }}>
              <Cpu size={10} style={{ color: '#93C5FD' }} />
              <p className="info-label" style={{ marginBottom:0 }}>Model</p>
            </div>
            <p className="info-value" style={{ fontSize:12, fontWeight:500 }}>{result.model}</p>
          </div>
        </div>


      </div>
    </div>
  )
}
