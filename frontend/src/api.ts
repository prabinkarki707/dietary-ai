// api.ts — Typed API client for the FastAPI backend

import axios from 'axios'

// In dev the Vite proxy forwards /ocr, /advise etc → localhost:8000
// In production set VITE_API_BASE to the deployed backend URL
const BASE = import.meta.env.VITE_API_BASE || ''

const api = axios.create({ baseURL: BASE })

export interface Profile {
  id: string
  name: string
  conditions: string[]
  hba1c: number
  glucose_fasting: number
  bp_systolic: number
  bp_diastolic: number
  egfr: number
  potassium: number
  allergens: string[]
}

export interface OcrResult {
  raw_text: string
  ocr_method: string
  ocr_confidence: string
  markers: {
    hba1c: number | null
    glucose_fasting: number | null
    bp_systolic: number | null
    bp_diastolic: number | null
    egfr: number | null
    potassium: number | null
    allergens: string[]
    confidence: Record<string, number>
  }
}

export interface RecogniseResult {
  top1: string
  top3: { label: string; score: number }[]
  error: string | null
}

export interface AdviseResult {
  verdict: 'recommend' | 'limit' | 'avoid' | 'unknown' | 'uncertain'
  reason: string
  confidence: string
  per_condition: Record<string, string>
  allergy_flag: boolean
  matrix_verdict: string
  llm_verdict: string
  latency_ms: number
  model: string
  strategy: string
  disclaimer: string
}

export const getProfiles = () => api.get<Profile[]>('/profiles').then(r => r.data)

export const uploadOcr = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<OcrResult>('/ocr', form).then(r => r.data)
}

export const recogniseFood = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<RecogniseResult>('/recognise', form).then(r => r.data)
}

export const getAdvice = (payload: {
  profile_id?: string
  conditions: string[]
  allergens: string[]
  hba1c?: number | null
  glucose_fasting?: number | null
  bp_systolic?: number | null
  bp_diastolic?: number | null
  egfr?: number | null
  potassium?: number | null
  food: string
  question?: string
  model: string
  strategy: string
}) => api.post<AdviseResult>('/advise', payload).then(r => r.data)
