import { useState } from 'react'
import { ScanText, BarChart2, FileText, ChevronDown, ChevronUp, CheckCircle2, AlertCircle } from 'lucide-react'
import UploadZone from '../components/UploadZone'
import { uploadOcr, type OcrResult } from '../api'

const MARKER_LABELS: Record<string, string> = {
  hba1c: 'HbA1c (mmol/mol)',
  glucose_fasting: 'Fasting Glucose',
  bp_systolic: 'Systolic BP',
  bp_diastolic: 'Diastolic BP',
  egfr: 'eGFR',
  potassium: 'Potassium',
}

const MARKER_UNITS: Record<string, string> = {
  hba1c: 'mmol/mol',
  glucose_fasting: 'mmol/L',
  bp_systolic: 'mmHg',
  bp_diastolic: 'mmHg',
  egfr: 'mL/min',
  potassium: 'mmol/L',
}

export default function ReportTab() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<OcrResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showRaw, setShowRaw] = useState(false)

  const run = async () => {
    if (!file) return
    setLoading(true); setError(null)
    try {
      setResult(await uploadOcr(file))
    } catch (e: unknown) {
      const msg = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(msg?.response?.data?.detail || msg?.message || 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const markers = (result?.markers || {}) as Record<string, unknown> & { allergens?: string[] }
  const foundCount = Object.entries(MARKER_LABELS).filter(([k]) => markers[k] != null).length

  return (
    <div style={{ padding:'26px 20px 20px' }}>
      <div className="page-header">
        <h1 className="page-title">Medical Report Analysis</h1>
        <p className="page-subtitle">Upload a blood test or clinical report to extract key health markers</p>
      </div>

      {/* Steps */}
      <div className="steps">
        <div className="step">
          <div className={`step-num ${result ? 'done' : 'active'}`}>{result ? '✓' : '1'}</div>
          <span className="step-label">Upload Report</span>
        </div>
        <div className="step-connector" />
        <div className="step">
          <div className={`step-num ${result ? 'active' : 'pending'}`}>2</div>
          <span className="step-label">Extract Markers</span>
        </div>
        <div className="step-connector" />
        <div className="step">
          <div className="step-num pending">3</div>
          <span className="step-label">Review Results</span>
        </div>
      </div>

      {/* Upload */}
      <div className="card">
        <div className="card-header">
          <div className="card-icon blue"><FileText size={18} /></div>
          <div>
            <p className="card-title">Upload Medical Report</p>
            <p className="card-subtitle">JPG, PNG or PDF · Processed via OCR · No data stored</p>
          </div>
        </div>
        <div className="card-body">
          <UploadZone
            onFileSelect={setFile}
            accept=".jpg,.jpeg,.png,.pdf"
            label="Drop your report here or click to browse"
            hint="JPG · PNG · PDF — max 10 MB"
          />
          {error && (
            <div className="error-box" style={{ marginTop: 12 }}>
              <AlertCircle size={16} style={{ flexShrink:0, marginTop:1 }} />
              <span>{error}</span>
            </div>
          )}
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={run} disabled={!file || loading}>
            {loading ? <><div className="spinner" />Extracting markers…</> : <><ScanText size={17} />Extract Markers</>}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <>
          {/* OCR status bar */}
          <div className="success-box" style={{ marginBottom: 16 }}>
            <CheckCircle2 size={16} style={{ flexShrink:0, marginTop:1 }} />
            <span>
              OCR completed via <strong>{result.ocr_method}</strong> — confidence: <strong>{result.ocr_confidence}</strong> · {foundCount} of {Object.keys(MARKER_LABELS).length} markers found
            </span>
          </div>

          {/* Markers grid */}
          <div className="card">
            <div className="card-header">
              <div className="card-icon blue"><BarChart2 size={18} /></div>
              <div>
                <p className="card-title">Extracted Clinical Markers</p>
                <p className="card-subtitle">Highlighted cells indicate successfully extracted values</p>
              </div>
            </div>
            <div className="card-body">
              <div className="markers-grid">
                {Object.entries(MARKER_LABELS).map(([key, label]) => {
                  const val = markers[key]
                  const conf = result.markers?.confidence?.[key === 'bp_systolic' || key === 'bp_diastolic' ? 'blood_pressure' : key] ?? 0
                  return (
                    <div key={key} className={`marker-cell ${val != null ? 'has-value' : ''}`}>
                      <p className="marker-name">{label}</p>
                      <p className={`marker-value ${val == null ? 'empty' : ''}`}>
                        {val != null ? `${val}` : '—'}
                        {val != null && <span style={{ fontSize:12, fontWeight:500, marginLeft:4 }}>{MARKER_UNITS[key]}</span>}
                      </p>
                      {val != null && (
                        <div className="confidence-bar-wrap">
                          <div
                            className="confidence-bar"
                            style={{
                              width: `${conf * 100}%`,
                              background: conf === 1 ? 'var(--green)' : conf >= 0.7 ? 'var(--amber)' : 'var(--red)',
                            }}
                          />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Allergens */}
              {(markers.allergens?.length ?? 0) > 0 && (
                <div style={{ marginTop: 16 }}>
                  <p className="section-heading">Allergens Detected</p>
                  {(markers.allergens ?? []).map((a: string) => (
                    <span key={a} className="chip chip-red">{a}</span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Raw OCR */}
          <div className="card">
            <div className="card-header" style={{ cursor:'pointer' }} onClick={() => setShowRaw(s => !s)}>
              <div className="card-icon blue"><FileText size={18} /></div>
              <div style={{ flex:1 }}>
                <p className="card-title">Raw OCR Text</p>
                <p className="card-subtitle">Full extracted text from the document</p>
              </div>
              {showRaw ? <ChevronUp size={18} color="var(--text-secondary)" /> : <ChevronDown size={18} color="var(--text-secondary)" />}
            </div>
            {showRaw && (
              <div className="card-body" style={{ paddingTop: 12 }}>
                <div className="raw-text-box">{result.raw_text || '(no text extracted)'}</div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
