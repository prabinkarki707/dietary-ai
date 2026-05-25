import { useState, useEffect } from 'react'
import { UserCircle2, MessageSquare, Sparkles, AlertCircle, Plus } from 'lucide-react'
import VerdictCard from '../components/VerdictCard'
import CustomProfileModal from '../components/CustomProfileModal'

import { getAdvice, getProfiles, type Profile, type AdviseResult } from '../api'

// Gender map for correct avatars
const FEMALE_NAMES = new Set(['Alice','Carol','Eve','Grace','Irene','Karen','Mary','Olivia'])
function avatarUrl(name: string, profileId: string) {
  const gender = FEMALE_NAMES.has(name.split(' ')[0]) ? 'women' : 'men'
  const num = parseInt(profileId.replace('P', ''), 10) || 1
  return `https://randomuser.me/api/portraits/${gender}/${num}.jpg`
}
function initials(name: string) { return name.split(' ').map(n => n[0]).join('').slice(0,2).toUpperCase() }

function ProfileListOnly({ profiles, selected, onSelect }: { profiles: Profile[], selected: Profile | null, onSelect: (p: Profile) => void }) {
  const [errors, setErrors] = useState<Record<string,boolean>>({})
  useEffect(() => { if (profiles.length > 0 && !selected) onSelect(profiles[0]) }, [profiles])
  const condLabel = (p: Profile) => p.conditions.length === 0
    ? 'No conditions'
    : p.conditions[0] + (p.conditions.length > 1 ? ` +${p.conditions.length-1}` : '')
  return (
    <div style={{ flex:1, overflowY:'auto' }}>
      {profiles.map(p => {
        const active = selected?.id === p.id
        const errored = errors[p.id]
        return (
          <div
            key={p.id}
            onClick={() => onSelect(p)}
            style={{
              display:'flex', alignItems:'center', gap:10, padding:'9px 12px',
              cursor:'pointer', borderBottom:'1px solid var(--border)',
              background: active ? 'var(--blue-light)' : 'transparent',
              borderLeft: active ? '2px solid var(--blue)' : '2px solid transparent',
              transition:'background 0.12s',
            }}
          >
            {!errored ? (
              <div style={{ width:30, height:30, borderRadius:'50%', overflow:'hidden', flexShrink:0, border:'1.5px solid var(--border-strong)' }}>
                <img src={avatarUrl(p.name, p.id)} alt={p.name} style={{ width:'100%', height:'100%', objectFit:'cover', display:'block' }}
                  onError={() => setErrors(prev => ({ ...prev, [p.id]: true }))} />
              </div>
            ) : (
              <div style={{ width:30, height:30, borderRadius:'50%', background:'var(--blue-light)', color:'var(--blue)', fontSize:11, fontWeight:700, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                {initials(p.name)}
              </div>
            )}
            <div style={{ minWidth:0 }}>
              <div style={{ fontSize:12, fontWeight:600, color:'var(--text-primary)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{p.name}</div>
              <div style={{ fontSize:10, color:'var(--text-tertiary)', marginTop:1 }}>{condLabel(p)}</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

const MODELS = [
  { value: 'claude-sonnet-4-5', label: 'Claude Sonnet 4.5 (fixed)' },
]

const STRATEGIES = [
  { value: 'structured_role', label: 'Structured Role' },
  { value: 'zero_shot', label: 'Zero-shot' },
  { value: 'few_shot', label: 'Few-shot' },
  { value: 'rag_grounded', label: 'RAG Grounded' },
]

const EXAMPLE_QUESTIONS = [
  'Is this safe for my kidneys?',
  'Can I eat this for breakfast?',
  'How often can I eat this?',
  'Are there healthier alternatives?',
  'Will this raise my blood sugar?',
]

export default function AdviceTab() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null)
  const [customProfiles, setCustomProfiles] = useState<Profile[]>([])
  const [showModal, setShowModal] = useState(false)
  const [food, setFood] = useState('')
  const [question, setQuestion] = useState('')
  const [model, setModel] = useState('claude-sonnet-4-5')
  const [strategy, setStrategy] = useState('structured_role')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AdviseResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => { getProfiles().then(setProfiles).catch(() => {}) }, [])

  const allProfiles = [...customProfiles, ...profiles]

  const handleSaveCustomProfile = (profile: Profile) => {
    setCustomProfiles(prev => [...prev, profile])
    setSelectedProfile(profile)
    setShowModal(false)
  }

  const submit = async () => {
    if (!selectedProfile || !food.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      setResult(await getAdvice({
        profile_id: selectedProfile.id,
        conditions: selectedProfile.conditions,
        allergens: selectedProfile.allergens,
        hba1c: selectedProfile.hba1c,
        glucose_fasting: selectedProfile.glucose_fasting,
        bp_systolic: selectedProfile.bp_systolic,
        bp_diastolic: selectedProfile.bp_diastolic,
        egfr: selectedProfile.egfr,
        potassium: selectedProfile.potassium,
        food: food.trim().toLowerCase().replace(/\s+/g, '_'),
        question: question || undefined,
        model, strategy,
      }))
    } catch (e: unknown) {
      const msg = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(msg?.response?.data?.detail || msg?.message || 'Request failed')
    } finally { setLoading(false) }
  }

  return (
    <>
    {showModal && (
      <CustomProfileModal
        onClose={() => setShowModal(false)}
        onSave={handleSaveCustomProfile}
      />
    )}
    <div style={{ display:'flex', flexDirection:'column', height:'calc(100vh - var(--navbar-height) - var(--tab-bar-height))', overflow:'hidden', padding:'18px 20px 0' }}>
      <div style={{ display:'flex', alignItems:'baseline', justifyContent:'space-between', marginBottom:12, flexShrink:0 }}>
        <div>
          <h1 className="page-title">Ask the AI</h1>
          <p className="page-subtitle">Choose a profile, enter a food and get personalised dietary advice</p>
        </div>
      </div>

      {/* Two-column layout: profile list left, form right */}
      <div style={{ display:'flex', gap:14, alignItems:'stretch', flex:1, minHeight:0, overflow:'hidden', paddingBottom:8 }}>

        {/* LEFT — Profile list */}
        <div style={{ width:220, flexShrink:0, display:'flex', flexDirection:'column' }}>
          <div className="card" style={{ marginBottom:0, flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
            <div className="card-header" style={{ padding:'12px 14px 10px', flexShrink:0 }}>
              <div className="card-icon blue"><UserCircle2 size={16} /></div>
              <div style={{ flex:1, minWidth:0 }}>
                <p className="card-title" style={{ fontSize:13 }}>Patient Profile</p>
              </div>
              <button
                onClick={() => setShowModal(true)}
                title="Create custom profile"
                style={{
                  display:'flex', alignItems:'center', gap:4, padding:'4px 8px',
                  background:'var(--blue-light)', border:'1px solid var(--blue)',
                  borderRadius:4, cursor:'pointer', color:'var(--blue)', fontSize:10, fontWeight:600, flexShrink:0,
                }}
              >
                <Plus size={12} /> New
              </button>
            </div>
            <div style={{ padding:0, flex:1, overflowY:'auto' }}>
              {allProfiles.length === 0
                ? <p style={{ color:'var(--text-secondary)', fontSize:13, padding:'12px 14px' }}>Backend offline</p>
                : <ProfileListOnly profiles={allProfiles} selected={selectedProfile} onSelect={setSelectedProfile} />
              }
            </div>
          </div>
        </div>

        {/* RIGHT — Ask form */}
        <div style={{ flex:1, minWidth:0, display:'flex', flexDirection:'column' }}>
          <div className="card" style={{ marginBottom: result ? 14 : 0, flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
            <div className="card-header" style={{ flexShrink:0 }}>
              <div className="card-icon blue"><MessageSquare size={18} /></div>
              <div>
                <p className="card-title">Ask About a Food</p>
                <p className="card-subtitle">
                  {selectedProfile
                    ? `Asking for ${selectedProfile.name}`
                    : 'Select a profile first'}
                </p>
              </div>
            </div>
            <div className="card-body" style={{ flex:1, overflowY:'auto' }}>
              <div className="form-group">
                <label className="form-label">Food Item</label>
                <input
                  className="form-input"
                  placeholder="e.g. grilled salmon, apple pie, white rice..."
                  value={food}
                  onChange={e => setFood(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  Your Question{' '}
                  <span style={{ color:'var(--text-tertiary)', fontWeight:400 }}>(optional)</span>
                </label>
                <textarea
                  className="form-textarea"
                  placeholder="e.g. Is this safe for my kidneys? Can I eat this daily?"
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  style={{ minHeight:66 }}
                />
              </div>

              {/* Quick questions */}
              <div style={{ marginBottom:14 }}>
                <p className="section-heading">Quick questions</p>
                <div style={{ display:'flex', flexWrap:'wrap', gap:5 }}>
                  {EXAMPLE_QUESTIONS.map(q => (
                    <button key={q} className="btn btn-secondary btn-sm" onClick={() => setQuestion(q)} style={{ fontWeight:400 }}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>

              {/* Model + strategy */}
              <div className="model-strategy-row">
                <div className="form-group" style={{ marginBottom:0 }}>
                  <label className="form-label">AI Model</label>
                  <select className="form-select" value={model} onChange={e => setModel(e.target.value)}>
                    {MODELS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom:0 }}>
                  <label className="form-label">Prompting Strategy</label>
                  <select className="form-select" value={strategy} onChange={e => setStrategy(e.target.value)}>
                    {STRATEGIES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                  </select>
                </div>
              </div>

              {error && (
                <div className="error-box" style={{ marginBottom:12 }}>
                  <AlertCircle size={16} style={{ flexShrink:0, marginTop:1 }} />
                  <span>{error}</span>
                </div>
              )}

              <button
                className="btn btn-primary"
                style={{ marginTop:4 }}
                onClick={submit}
                disabled={!selectedProfile || !food.trim() || loading}
              >
                {loading
                  ? <><div className="spinner" />Getting advice…</>
                  : <><Sparkles size={17} />Get Dietary Advice</>}
              </button>
            </div>
          </div>

          {result && <VerdictCard result={result} food={food} />}
        </div>
      </div>

      {/* Disclaimer */}
      <p style={{ textAlign:'right', fontSize:11, color:'var(--text-tertiary)', padding:'4px 0 6px', flexShrink:0 }}>
        AI-generated advice only. Not a substitute for professional medical or dietetic consultation.
      </p>
    </div>
    </>
  )
}
