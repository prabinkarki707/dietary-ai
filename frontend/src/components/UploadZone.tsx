import { useState, useRef } from 'react'
import { Upload, CheckCircle2 } from 'lucide-react'

interface Props {
  onFileSelect: (file: File) => void
  accept?: string
  label?: string
  hint?: string
}

export default function UploadZone({ onFileSelect, accept = 'image/*', label = 'Upload image', hint = 'JPG, PNG supported' }: Props) {
  const [fileName, setFileName] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (file: File) => {
    setFileName(file.name)
    onFileSelect(file)
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div
      className={`upload-zone ${fileName ? 'has-file' : ''}`}
      onClick={() => inputRef.current?.click()}
      onDrop={onDrop}
      onDragOver={e => e.preventDefault()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={e => {
          const file = e.target.files?.[0]
          if (file) handleFile(file)
        }}
      />
      <div className="upload-icon">
        {fileName ? <CheckCircle2 size={22} /> : <Upload size={22} />}
      </div>
      <p className="upload-text">{fileName ? fileName : label}</p>
      <p className="upload-hint">{fileName ? 'Click to change file' : hint}</p>
    </div>
  )
}
