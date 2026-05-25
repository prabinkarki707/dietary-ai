import { useEffect, useState } from 'react'
import { User, Heart, AlertCircle } from 'lucide-react'
import type { Profile } from '../api'

// Gender mapping from data/profiles.json
const FEMALE_NAMES = new Set(['Alice','Carol','Eve','Grace','Irene','Karen','Mary','Olivia'])

function avatarUrl(name: string, profileId: string): string {
  const firstName = name.split(' ')[0]
  const gender = FEMALE_NAMES.has(firstName) ? 'women' : 'men'
  const num = parseInt(profileId.replace('P', ''), 10) || 1
  return `https://randomuser.me/api/portraits/${gender}/${num}.jpg`
}

function initials(name: string) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

interface Props {
  profiles: Profile[]
  selected: Profile | null
  onSelect: (p: Profile) => void
}

export default function ProfileSelector({ profiles, selected, onSelect }: Props) {
  const [imgErrors, setImgErrors] = useState<Record<string, boolean>>({})

  useEffect(() => {
    if (profiles.length > 0 && !selected) {
      onSelect(profiles[0])
    }
  }, [profiles])

  function handleImgError(id: string) {
    setImgErrors(prev => ({ ...prev, [id]: true }))
  }

  return (
    <div className="profile-picker">
      {/* Left sidebar */}
      <div className="profile-list">
        {profiles.map(p => {
          const url = avatarUrl(p.name, p.id)
          const errored = imgErrors[p.id]
          const isActive = selected?.id === p.id
          const condLabel = p.conditions.length === 0
            ? 'No conditions'
            : p.conditions[0] + (p.conditions.length > 1 ? ` +${p.conditions.length - 1}` : '')
          return (
            <div
              key={p.id}
              className={`profile-list-item${isActive ? ' active' : ''}`}
              onClick={() => onSelect(p)}
            >
              {!errored ? (
                <div className="profile-list-avatar">
                  <img src={url} alt={p.name} onError={() => handleImgError(p.id)} />
                </div>
              ) : (
                <div className="profile-list-avatar-fb">{initials(p.name)}</div>
              )}
              <div>
                <div className="profile-list-name">{p.name}</div>
                <div className="profile-list-cond">{condLabel}</div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Right detail panel */}
      <div className="profile-detail">
        {!selected ? (
          <div className="profile-no-selection">
            <User size={28} />
            <span>Select a profile</span>
          </div>
        ) : (
          <>
            <div className="profile-detail-header">
              {!imgErrors[selected.id] ? (
                <div className="profile-detail-avatar">
                  <img
                    src={avatarUrl(selected.name, selected.id)}
                    alt={selected.name}
                    onError={() => handleImgError(selected.id)}
                  />
                </div>
              ) : (
                <div className="profile-detail-avatar-fb">{initials(selected.name)}</div>
              )}
              <div>
                <div className="profile-detail-name">{selected.name}</div>
                <div className="profile-detail-id">Profile ID: {selected.id}</div>
              </div>
            </div>

            <div className="profile-stats">
              <div className="profile-stat">
                <div className="profile-stat-label">HbA1c</div>
                <div className="profile-stat-value">{selected.hba1c != null ? `${selected.hba1c}%` : '—'}</div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat-label">Glucose</div>
                <div className="profile-stat-value">{selected.glucose_fasting != null ? selected.glucose_fasting : '—'}</div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat-label">eGFR</div>
                <div className="profile-stat-value">{selected.egfr != null ? selected.egfr : '—'}</div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat-label">BP</div>
                <div className="profile-stat-value">
                  {selected.bp_systolic != null ? `${selected.bp_systolic}/${selected.bp_diastolic}` : '—'}
                </div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat-label">K⁺</div>
                <div className="profile-stat-value">{selected.potassium != null ? selected.potassium : '—'}</div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat-label">Conditions</div>
                <div className="profile-stat-value">{selected.conditions.length}</div>
              </div>
            </div>

            <div style={{ marginBottom: 12 }}>
              <div className="section-heading" style={{ display:'flex', alignItems:'center', gap:5 }}>
                <Heart size={10} /> Health Conditions
              </div>
              {selected.conditions.length === 0 ? (
                <span className="chip chip-gray">No health conditions</span>
              ) : (
                <div>{selected.conditions.map(c => <span key={c} className="chip chip-red">{c}</span>)}</div>
              )}
            </div>

            {selected.allergens && selected.allergens.length > 0 && (
              <div>
                <div className="section-heading" style={{ display:'flex', alignItems:'center', gap:5 }}>
                  <AlertCircle size={10} /> Allergens
                </div>
                <div>{selected.allergens.map(a => <span key={a} className="chip chip-amber">{a}</span>)}</div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
