<div align="center">

# 🥗 DietaryAI

**AI-powered dietary advice for people living with chronic conditions**

Built as part of my BSc dissertation at York St John University (COM6016M, 2025-26)

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Claude](https://img.shields.io/badge/Claude-Sonnet_4.5-orange?style=flat-square)](https://anthropic.com)
[![Live](https://img.shields.io/badge/Live-prabinkarki.com%2Fdietaryai-brightgreen?style=flat-square)](https://prabinkarki.com/dietaryai)

---

**[🚀 Try the live app](https://prabinkarki.com/dietaryai)** · **[👤 About me](https://prabinkarki.com)** · **[📧 Get in touch](mailto:prabin@daodial.com)**

</div>

---

## What does it do?

You upload a medical report image (blood test, GP letter etc.), the app extracts your clinical markers, figures out your conditions (diabetes, hypertension, CKD), and then tells you whether a specific food is suitable for you or not. It uses Claude to generate the actual advice and a manually built safety matrix as a guardrail so the AI can't recommend something dangerous.

The whole thing is a research prototype, not a medical product. All verdicts come with a disclaimer and the safety matrix always wins over the LLM if they disagree.

---

## How it works

```
Medical Report → OCR → Marker Extraction → Condition Inference
                                                    ↓
Food Image → Food-101 ViT Model → Food Label → Safety Check (deterministic)
                                                    ↓
                                             LLM Advice (Claude)
                                                    ↓
                                        Verdict + Reason + Disclaimer
```

Four different prompting strategies were tested: `zero_shot`, `structured_role`, `few_shot`, and `rag_grounded`. The RAG strategy came out 7.5 percentage points ahead of the others in accuracy against an 88-food gold standard matrix.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Python 3.11, Uvicorn |
| LLM | Claude Sonnet 4.5 via Anthropic API |
| OCR | Tesseract + pdfminer |
| Food recognition | ViT fine-tuned on Food-101 (HuggingFace transformers) |
| RAG | FAISS + sentence-transformers (all-MiniLM-L6-v2) |
| Guidelines | NICE NG28, NICE NG136, KDOQI 2020 |
| Frontend | React 18, Vite, TypeScript |
| Database | SQLite (audit log) |
| Deployment | AWS Elastic Beanstalk (backend) + S3/CloudFront (frontend) |

---

## Running locally

**Backend**

```bash
git clone https://github.com/prabinkarki707/dietary-ai.git
cd dietary-ai

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "ANTHROPIC_API_KEY=your_key_here" > .env

uvicorn backend.main:app --reload
# → http://localhost:8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

The frontend proxies all API calls to `localhost:8000` in dev mode so no extra config needed.

---

## Project structure

```
dietary-ai/
├── backend/
│   ├── main.py              # FastAPI app, all endpoints
│   ├── ocr.py               # Tesseract OCR
│   ├── markers.py           # Clinical marker extraction
│   ├── conditions.py        # NICE/KDOQI condition inference
│   ├── food_recognition.py  # ViT food classifier
│   ├── safety_check.py      # Gold-standard matrix lookup
│   ├── llm_router.py        # Claude API + strategy selector
│   ├── prompts.py           # All 4 prompting strategies
│   ├── rag.py               # FAISS retrieval
│   └── logger_db.py         # SQLite audit log
├── data/
│   ├── gold_standard.csv          # 88 foods x 4 conditions
│   ├── profiles.json              # Synthetic patient profiles
│   └── guidelines/
│       └── guidelines_chunks.txt  # RAG corpus (NICE + KDOQI)
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── api.ts
│       └── tabs/            # Report, Food, Advice tabs
├── harness/
│   └── run_batch_claude.py  # Experiment harness (1440 queries)
├── results/
│   ├── raw.csv              # Full experiment results
│   └── metrics.json         # Computed accuracy metrics
└── tests/                   # pytest unit tests
```

---

## Experiment results

Ran 1,440 queries across 4 strategies against claude-sonnet-4-5. Key findings:

- **RAG: 60.8% accuracy** vs 53.3% for the next best (few_shot)
- **0% unsafe rate** across all strategies (model never recommended an "avoid" food)
- **CKD accuracy was notably lower** (40.2%) compared to diabetes (60.6%) across all strategies
- Statistical significance confirmed via McNemar's test (p < 0.05 for RAG vs others)

---

## Disclaimer

This is a research project. Nothing in this app should be taken as medical advice. Always consult a qualified dietitian or your GP before making dietary changes.

---

<div align="center">

Made by **Prabin Karki** · BSc Computing · York St John University · 2026

[prabinkarki.com](https://prabinkarki.com) · [LinkedIn](https://linkedin.com/in/prabinkarki707) · [prabin@daodial.com](mailto:prabin@daodial.com)

</div>
