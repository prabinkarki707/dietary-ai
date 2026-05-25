import { useState, useEffect } from 'react'
import { UserCircle2, Camera, Sparkles, AlertCircle, Brain, Plus } from 'lucide-react'
import UploadZone from '../components/UploadZone'
import VerdictCard from '../components/VerdictCard'
import CustomProfileModal from '../components/CustomProfileModal'
import { recogniseFood, getAdvice, getProfiles, type Profile, type RecogniseResult, type AdviseResult } from '../api'

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
    <div style={{ overflowY:'auto', flex:1 }}>
      {profiles.map(p => {
        const active = selected?.id === p.id
        const errored = errors[p.id]
        return (
          <div key={p.id} onClick={() => onSelect(p)} style={{
            display:'flex', alignItems:'center', gap:10, padding:'9px 12px',
            cursor:'pointer', borderBottom:'1px solid var(--border)',
            background: active ? 'var(--blue-light)' : 'transparent',
            borderLeft: active ? '2px solid var(--blue)' : '2px solid transparent',
            transition:'background 0.12s',
          }}>
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

export default function FoodTab() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null)
  const [customProfiles, setCustomProfiles] = useState<Profile[]>([])
  const [showModal, setShowModal] = useState(false)
  const [foodFile, setFoodFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [recogResult, setRecogResult] = useState<RecogniseResult | null>(null)
  const [adviseResult, setAdviseResult] = useState<AdviseResult | null>(null)
  const [model, setModel] = useState('claude-sonnet-4-5')
  const [strategy, setStrategy] = useState('structured_role')
  const [loading, setLoading] = useState(false)
  const [loadingAdvice, setLoadingAdvice] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => { getProfiles().then(setProfiles).catch(() => {}) }, [])

  const allProfiles = [...customProfiles, ...profiles]

  const handleSaveCustomProfile = (profile: Profile) => {
    setCustomProfiles(prev => [...prev, profile])
    setSelectedProfile(profile)
    setShowModal(false)
  }

  const handleFoodFile = (file: File) => {
    setFoodFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setRecogResult(null); setAdviseResult(null)
  }

  const recognise = async () => {
    if (!foodFile) return
    setLoading(true); setError(null)
    try {
      setRecogResult(await recogniseFood(foodFile))
    } catch (e: unknown) {
      const msg = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(msg?.response?.data?.detail || msg?.message || 'Recognition failed')
    } finally { setLoading(false) }
  }

  const advise = async () => {
    if (!recogResult || !selectedProfile) return
    setLoadingAdvice(true); setError(null)
    try {
      const r = await getAdvice({
        profile_id: selectedProfile.id,
        conditions: selectedProfile.conditions,
        allergens: selectedProfile.allergens,
        hba1c: selectedProfile.hba1c,
        glucose_fasting: selectedProfile.glucose_fasting,
        bp_systolic: selectedProfile.bp_systolic,
        bp_diastolic: selectedProfile.bp_diastolic,
        egfr: selectedProfile.egfr,
        potassium: selectedProfile.potassium,
        food: recogResult.top1,
        model, strategy,
      })
      setAdviseResult(r)
    } catch (e: unknown) {
      const msg = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(msg?.response?.data?.detail || msg?.message || 'Advice request failed')
    } finally { setLoadingAdvice(false) }
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
      <div style={{ marginBottom:12, flexShrink:0 }}>
        <h1 className="page-title">Food Safety Check</h1>
        <p className="page-subtitle">Upload a food photo — AI identifies it and assesses suitability for your conditions</p>
      </div>

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
            <div style={{ padding:0, flex:1, overflowY:'auto', display:'flex', flexDirection:'column' }}>
              {allProfiles.length === 0
                ? <p style={{ color:'var(--text-secondary)', fontSize:13, padding:'12px 14px' }}>Backend offline</p>
                : <ProfileListOnly profiles={allProfiles} selected={selectedProfile} onSelect={p => { setSelectedProfile(p); setRecogResult(null); setAdviseResult(null) }} />
              }
            </div>
          </div>
        </div>

        {/* RIGHT — Food flow */}
        <div style={{ flex:1, minWidth:0, display:'flex', flexDirection:'column' }}>
          <div className="card" style={{ marginBottom: adviseResult ? 14 : 0, flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
            <div className="card-header" style={{ flexShrink:0 }}>
              <div className="card-icon blue"><Camera size={18} /></div>
              <div>
                <p className="card-title">Food Safety Check</p>
                <p className="card-subtitle">
                  {selectedProfile ? `Checking for ${selectedProfile.name}` : 'Select a profile first'}
                </p>
              </div>
            </div>
            <div style={{ flex:1, overflowY:'auto', padding:'18px 20px' }}>
              {previewUrl && <img src={previewUrl} alt="Food preview" className="food-preview" />}
              <UploadZone
                onFileSelect={handleFoodFile}
                accept=".jpg,.jpeg,.png,.webp"
                label="Drop a food photo or click to browse"
                hint="JPG · PNG · WebP"
              />
              {error && (
                <div className="error-box" style={{ marginTop:12 }}>
                  <AlertCircle size={16} style={{ flexShrink:0, marginTop:1 }} />
                  <span>{error}</span>
                </div>
              )}
              <button className="btn btn-primary" style={{ marginTop:16 }} onClick={recognise} disabled={!foodFile || loading || !selectedProfile}>
                {loading ? <><div className="spinner" />Identifying food…</> : <><Brain size={17} />Identify Food</>}
              </button>

              {/* Recognition result */}
              {recogResult && (
                <div style={{ marginTop:16 }}>
                  <div style={{ marginBottom:14, padding:'14px 16px', background:'var(--blue-light)', borderRadius:'var(--radius-sm)', border:'1px solid rgba(0,113,227,0.2)' }}>
                    <p className="section-heading" style={{ marginBottom:4 }}>Identified as</p>
                    <p style={{ fontSize:18, fontWeight:800, color:'var(--blue)', letterSpacing:'-0.4px', textTransform:'capitalize' }}>
                      {recogResult.top1.replace(/_/g, ' ')}
                    </p>
                    <div style={{ marginTop:8 }}>
                      {recogResult.top3.map(r => (
                        <span key={r.label} className="chip chip-blue">
                          {r.label.replace(/_/g, ' ')} {(r.score * 100).toFixed(0)}%
                        </span>
                      ))}
                    </div>
                  </div>

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

                  <button className="btn btn-primary" style={{ marginTop:8 }} onClick={advise} disabled={loadingAdvice}>
                    {loadingAdvice ? <><div className="spinner" />Analysing with AI…</> : <><Sparkles size={17} />Get Dietary Advice</>}
                  </button>
                </div>
              )}

              {adviseResult && <VerdictCard result={adviseResult} food={recogResult?.top1 || ''} />}
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  )
}