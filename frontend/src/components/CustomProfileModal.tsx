import { useState } from 'react'
import { X, ChevronRight, ChevronLeft, Check, User } from 'lucide-react'
import type { Profile } from '../api'

// ── Static option lists ────────────────────────────────────────────────────

const CONDITION_OPTIONS = [
  { value: 'diabetes',       label: 'Type 2 Diabetes (T2DM)',  desc: 'High blood sugar / insulin resistance' },
  { value: 'hypertension',   label: 'Hypertension',            desc: 'High blood pressure' },
  { value: 'ckd',            label: 'Chronic Kidney Disease',  desc: 'Reduced kidney function' },
  { value: 'hyperlipidemia', label: 'Hyperlipidaemia',         desc: 'High cholesterol / triglycerides' },
  { value: 'obesity',        label: 'Obesity',                 desc: 'BMI ≥ 30' },
  { value: 'heart_disease',  label: 'Heart Disease',           desc: 'Coronary artery disease / heart failure' },
  { value: 'gout',           label: 'Gout',                    desc: 'High uric acid / joint pain' },
]

const ALLERGEN_OPTIONS = [
  'Gluten', 'Dairy', 'Eggs', 'Nuts', 'Peanuts',
  'Shellfish', 'Fish', 'Soy', 'Sesame', 'Wheat',
]

const STEPS = ['Conditions', 'Allergens', 'Clinical Values', 'Done']

interface Props {
  onClose: () => void
  onSave: (profile: Profile) => void
}

export default function CustomProfileModal({ onClose, onSave }: Props) {
  const [step, setStep] = useState(0)
  const [name, setName]               = useState('')
  const [conditions, setConditions]   = useState<string[]>([])
  const [allergens, setAllergens]     = useState<string[]>([])
  const [hba1c, setHba1c]             = useState('')
  const [glucose, setGlucose]         = useState('')
  const [bpSys, setBpSys]             = useState('')
  const [bpDia, setBpDia]             = useState('')
  const [egfr, setEgfr]               = useState('')
  const [potassium, setPotassium]     = useState('')

  const toggleCondition = (v: string) =>
    setConditions(c => c.includes(v) ? c.filter(x => x !== v) : [...c, v])

  const toggleAllergen = (v: string) =>
    setAllergens(a => a.includes(v) ? a.filter(x => x !== v) : [...a, v])

  const handleSave = () => {
    const profile: Profile = {
      id: `custom-${Date.now()}`,
      name: name.trim() || 'My Profile',
      conditions,
      allergens,
      hba1c: hba1c ? parseFloat(hba1c) : 0,
      glucose_fasting: glucose ? parseFloat(glucose) : 0,
      bp_systolic: bpSys ? parseInt(bpSys) : 0,
      bp_diastolic: bpDia ? parseInt(bpDia) : 0,
      egfr: egfr ? parseFloat(egfr) : 0,
      potassium: potassium ? parseFloat(potassium) : 0,
    }
    onSave(profile)
  }

  const canNext = step === 0 ? name.trim().length > 0 : true

  return (
    <div style={{
      position:'fixed', inset:0, zIndex:500,
      background:'rgba(0,0,0,0.45)', backdropFilter:'blur(4px)',
      display:'flex', alignItems:'center', justifyContent:'center',
      padding:20,
    }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{
        background:'var(--surface)', borderRadius:8, width:'100%', maxWidth:480,
        boxShadow:'0 20px 60px rgba(0,0,0,0.2)', display:'flex', flexDirection:'column',
        maxHeight:'90vh', overflow:'hidden',
      }}>
        {/* Header */}
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 20px', borderBottom:'1px solid var(--border)', flexShrink:0 }}>
          <div>
            <p style={{ fontWeight:700, fontSize:15, color:'var(--text-primary)' }}>Create Custom Profile</p>
            <p style={{ fontSize:11, color:'var(--text-tertiary)', marginTop:2 }}>Step {step + 1} of {STEPS.length}: {STEPS[step]}</p>
          </div>
          <button onClick={onClose} style={{ background:'none', border:'none', cursor:'pointer', color:'var(--text-secondary)', padding:4, display:'flex' }}>
            <X size={18} />
          </button>
        </div>

        {/* Progress bar */}
        <div style={{ height:3, background:'var(--border)', flexShrink:0 }}>
          <div style={{ height:'100%', background:'var(--blue)', width:`${((step + 1) / STEPS.length) * 100}%`, transition:'width 0.3s' }} />
        </div>

        {/* Body */}
        <div style={{ flex:1, overflowY:'auto', padding:'20px' }}>

          {/* Step 0 — Name + Conditions */}
          {step === 0 && (
            <div>
              <div style={{ marginBottom:20 }}>
                <label style={{ fontSize:12, fontWeight:600, color:'var(--text-secondary)', display:'block', marginBottom:6 }}>
                  Your Name <span style={{ color:'var(--red)' }}>*</span>
                </label>
                <div style={{ display:'flex', alignItems:'center', gap:8, background:'var(--surface-2)', border:'1px solid var(--border)', borderRadius:4, padding:'0 10px' }}>
                  <User size={14} color='var(--text-tertiary)' />
                  <input
                    style={{ flex:1, background:'none', border:'none', outline:'none', padding:'9px 0', fontSize:13, color:'var(--text-primary)' }}
                    placeholder="e.g. John Smith"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    autoFocus
                  />
                </div>
              </div>

              <label style={{ fontSize:12, fontWeight:600, color:'var(--text-secondary)', display:'block', marginBottom:8 }}>
                Medical Conditions <span style={{ color:'var(--text-tertiary)', fontWeight:400 }}>(select all that apply)</span>
              </label>
              <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
                {CONDITION_OPTIONS.map(c => {
                  const active = conditions.includes(c.value)
                  return (
                    <div key={c.value} onClick={() => toggleCondition(c.value)} style={{
                      display:'flex', alignItems:'center', gap:10, padding:'9px 12px',
                      border:`1.5px solid ${active ? 'var(--blue)' : 'var(--border)'}`,
                      borderRadius:4, cursor:'pointer',
                      background: active ? 'var(--blue-light)' : 'var(--surface-2)',
                      transition:'all 0.12s',
                    }}>
                      <div style={{
                        width:18, height:18, borderRadius:3, flexShrink:0,
                        border:`1.5px solid ${active ? 'var(--blue)' : 'var(--border-strong)'}`,
                        background: active ? 'var(--blue)' : 'transparent',
                        display:'flex', alignItems:'center', justifyContent:'center',
                        transition:'all 0.12s',
                      }}>
                        {active && <Check size={11} color="#fff" strokeWidth={3} />}
                      </div>
                      <div>
                        <p style={{ fontSize:12, fontWeight:600, color:'var(--text-primary)' }}>{c.label}</p>
                        <p style={{ fontSize:10, color:'var(--text-tertiary)', marginTop:1 }}>{c.desc}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Step 1 — Allergens */}
          {step === 1 && (
            <div>
              <p style={{ fontSize:13, color:'var(--text-secondary)', marginBottom:14 }}>
                Select any foods you are allergic or intolerant to.
                <br /><span style={{ fontSize:11, color:'var(--text-tertiary)' }}>Skip this step if you have no known allergies.</span>
              </p>
              <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
                {ALLERGEN_OPTIONS.map(a => {
                  const active = allergens.includes(a)
                  return (
                    <button key={a} onClick={() => toggleAllergen(a)} style={{
                      padding:'6px 14px', borderRadius:99, fontSize:12, fontWeight:500,
                      border:`1.5px solid ${active ? 'var(--blue)' : 'var(--border)'}`,
                      background: active ? 'var(--blue)' : 'var(--surface-2)',
                      color: active ? '#fff' : 'var(--text-primary)',
                      cursor:'pointer', transition:'all 0.12s',
                    }}>
                      {a}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Step 2 — Clinical values (optional) */}
          {step === 2 && (
            <div>
              <p style={{ fontSize:13, color:'var(--text-secondary)', marginBottom:16 }}>
                Enter your latest clinical values for more accurate advice.
                <br /><span style={{ fontSize:11, color:'var(--text-tertiary)' }}>All fields are optional — skip if you don't know them.</span>
              </p>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
                {[
                  { label:'HbA1c (%)',       placeholder:'e.g. 7.2',  value:hba1c,     set:setHba1c,     hint:'Normal < 5.7%' },
                  { label:'Fasting Glucose (mmol/L)', placeholder:'e.g. 6.1', value:glucose, set:setGlucose, hint:'Normal 3.9–5.6' },
                  { label:'BP Systolic (mmHg)',  placeholder:'e.g. 130', value:bpSys,    set:setBpSys,     hint:'Normal < 120' },
                  { label:'BP Diastolic (mmHg)', placeholder:'e.g. 85',  value:bpDia,    set:setBpDia,     hint:'Normal < 80' },
                  { label:'eGFR (mL/min)',    placeholder:'e.g. 75',   value:egfr,      set:setEgfr,      hint:'Normal ≥ 60' },
                  { label:'Potassium (mmol/L)', placeholder:'e.g. 4.2', value:potassium, set:setPotassium, hint:'Normal 3.5–5.0' },
                ].map(f => (
                  <div key={f.label}>
                    <label style={{ fontSize:11, fontWeight:600, color:'var(--text-secondary)', display:'block', marginBottom:4 }}>{f.label}</label>
                    <input
                      type="number"
                      step="any"
                      placeholder={f.placeholder}
                      value={f.value}
                      onChange={e => f.set(e.target.value)}
                      style={{
                        width:'100%', padding:'8px 10px', fontSize:12,
                        background:'var(--surface-2)', border:'1px solid var(--border)',
                        borderRadius:4, color:'var(--text-primary)', outline:'none',
                      }}
                    />
                    <p style={{ fontSize:10, color:'var(--text-tertiary)', marginTop:3 }}>{f.hint}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 3 — Summary */}
          {step === 3 && (
            <div style={{ textAlign:'center', padding:'10px 0 4px' }}>
              <div style={{ width:60, height:60, borderRadius:'50%', background:'var(--blue-light)', display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 14px' }}>
                <Check size={28} color='var(--blue)' strokeWidth={2.5} />
              </div>
              <p style={{ fontSize:16, fontWeight:700, color:'var(--text-primary)', marginBottom:6 }}>{name.trim() || 'My Profile'}</p>
              <div style={{ display:'flex', flexWrap:'wrap', gap:5, justifyContent:'center', marginBottom:10 }}>
                {conditions.length === 0
                  ? <span style={{ fontSize:12, color:'var(--text-tertiary)' }}>No conditions selected</span>
                  : conditions.map(c => (
                    <span key={c} style={{ fontSize:11, padding:'3px 10px', borderRadius:99, background:'var(--blue-light)', color:'var(--blue)', fontWeight:500 }}>
                      {CONDITION_OPTIONS.find(o => o.value === c)?.label ?? c}
                    </span>
                  ))
                }
              </div>
              {allergens.length > 0 && (
                <div style={{ display:'flex', flexWrap:'wrap', gap:5, justifyContent:'center', marginBottom:10 }}>
                  {allergens.map(a => (
                    <span key={a} style={{ fontSize:11, padding:'3px 10px', borderRadius:99, background:'var(--amber-light)', color:'var(--amber)', fontWeight:500 }}>
                      {a}
                    </span>
                  ))}
                </div>
              )}
              <p style={{ fontSize:12, color:'var(--text-tertiary)' }}>Your profile is ready. Tap <strong>Save Profile</strong> to use it.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ display:'flex', gap:8, padding:'14px 20px', borderTop:'1px solid var(--border)', flexShrink:0 }}>
          {step > 0 && (
            <button onClick={() => setStep(s => s - 1)} style={{
              display:'flex', alignItems:'center', gap:5, padding:'8px 16px', fontSize:13, fontWeight:500,
              background:'var(--surface-2)', border:'1px solid var(--border)', borderRadius:4,
              cursor:'pointer', color:'var(--text-secondary)',
            }}>
              <ChevronLeft size={15} /> Back
            </button>
          )}
          <div style={{ flex:1 }} />
          {step < STEPS.length - 1 ? (
            <button
              onClick={() => setStep(s => s + 1)}
              disabled={!canNext}
              style={{
                display:'flex', alignItems:'center', gap:5, padding:'8px 20px', fontSize:13, fontWeight:600,
                background: canNext ? 'var(--blue)' : 'var(--border)', border:'none', borderRadius:4,
                cursor: canNext ? 'pointer' : 'not-allowed', color: canNext ? '#fff' : 'var(--text-tertiary)',
                transition:'all 0.15s',
              }}>
              {step === 1 ? (allergens.length === 0 ? 'Skip' : 'Next') : 'Next'} <ChevronRight size={15} />
            </button>
          ) : (
            <button onClick={handleSave} style={{
              display:'flex', alignItems:'center', gap:6, padding:'8px 20px', fontSize:13, fontWeight:600,
              background:'var(--blue)', border:'none', borderRadius:4, cursor:'pointer', color:'#fff',
            }}>
              <Check size={15} /> Save Profile
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
