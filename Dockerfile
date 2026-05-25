# Use PyTorch CPU base image to avoid ~10 min build time for torch install
FROM pytorch/pytorch:2.3.0-cuda11.8-cudnn8-runtime

# Install system dependencies for Tesseract OCR and PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements.txt .

# Install remaining Python dependencies (torch already installed in base image)
RUN pip install --no-cache-dir \
    anthropic>=0.25.0 \
    fastapi>=0.111.0 \
    "uvicorn[standard]>=0.29.0" \
    python-multipart>=0.0.9 \
    pydantic>=2.7.0 \
    pytesseract>=0.3.10 \
    Pillow>=10.3.0 \
    pdf2image>=1.17.0 \
    "transformers>=4.41.0" \
    torchvision>=0.18.0 \
    "sentence-transformers>=3.0.0" \
    "faiss-cpu>=1.8.0" \
    pandas>=2.2.0 \
    "scikit-learn>=1.5.0" \
    python-dotenv>=1.0.0 \
    requests>=2.32.0 \
    numpy>=1.26.0

# Copy application code
COPY backend/ ./backend/
COPY data/ ./data/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
