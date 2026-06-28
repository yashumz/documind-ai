import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'

const API_BASE = '/api/v1'


export default function UploadZone({ onSuccess, currentDoc }) {
  const [uploading, setUploading] = useState(false)
  const [progress,  setProgress]  = useState(null)
  const [error,     setError]     = useState(null)

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return
    if (!file.name.endsWith('.pdf')) {
      setError('Only PDF files are supported')
      return
    }

    setUploading(true)
    setError(null)
    setProgress('Uploading to S3...')

    try {
      const formData = new FormData()
      formData.append('file', file)

      setProgress('Parsing document...')
      const response = await axios.post(`${API_BASE}/ingest`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setProgress('Indexing complete!')
      setTimeout(() => {
        setUploading(false)
        setProgress(null)
        onSuccess(response.data)
      }, 800)

    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
      setUploading(false)
      setProgress(null)
    }
  }, [onSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: uploading,
  })

  /* ── Compact mode (sidebar) ── */
  if (currentDoc) {
    return (
      <div style={{ padding: '20px' }}>
        {/* Current doc info */}
        <div style={{
          padding:      '16px',
          borderRadius: 'var(--radius-md)',
          background:   'var(--bg-elevated)',
          border:       '1px solid var(--border)',
          marginBottom: '20px',
          animation:    'fade-in 0.3s ease',
        }}>
          <div style={{
            fontSize:   '11px',
            color:      'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            marginBottom: '8px',
          }}>ACTIVE DOCUMENT</div>

          <div style={{
            fontFamily:   'var(--font-display)',
            fontWeight:   600,
            fontSize:     '14px',
            color:        'var(--text-primary)',
            marginBottom: '12px',
            wordBreak:    'break-all',
          }}>{currentDoc.filename}</div>

          {/* Chunk stats */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            {[
              { label: 'Total chunks',  value: currentDoc.total_chunks, color: 'var(--accent)' },
              { label: 'Text blocks',   value: currentDoc.text_chunks,  color: 'var(--success)' },
              { label: 'Tables',        value: currentDoc.table_chunks, color: 'var(--warning)' },
              { label: 'Images',        value: currentDoc.image_chunks, color: '#EC4899' },
            ].map(stat => (
              <div key={stat.label} style={{
                padding:      '10px',
                borderRadius: 'var(--radius-sm)',
                background:   'var(--bg-surface)',
                border:       '1px solid var(--border)',
              }}>
                <div style={{
                  fontSize:     '18px',
                  fontWeight:   700,
                  fontFamily:   'var(--font-mono)',
                  color:        stat.color,
                }}>{stat.value}</div>
                <div style={{
                  fontSize:     '10px',
                  color:        'var(--text-muted)',
                  marginTop:    '2px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Upload another */}
        <div {...getRootProps()} style={{
          padding:      '16px',
          borderRadius: 'var(--radius-md)',
          border:       `1px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`,
          textAlign:    'center',
          cursor:       'pointer',
          transition:   'all 0.2s ease',
          background:   isDragActive ? 'var(--accent-dim)' : 'transparent',
        }}>
          <input {...getInputProps()} />
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {uploading ? progress : 'Drop another PDF to replace'}
          </div>
        </div>

        {error && (
          <div style={{
            marginTop:    '12px',
            padding:      '10px 14px',
            borderRadius: 'var(--radius-sm)',
            background:   'rgba(239,68,68,0.1)',
            border:       '1px solid rgba(239,68,68,0.3)',
            fontSize:     '12px',
            color:        'var(--error)',
          }}>{error}</div>
        )}
      </div>
    )
  }

  /* ── Full centred mode (initial) ── */
  return (
    <div style={{ width: '100%', maxWidth: '520px' }}>
      {/* Hero heading */}
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <div style={{
          display:        'inline-flex',
          alignItems:     'center',
          gap:            '8px',
          padding:        '6px 14px',
          borderRadius:   '99px',
          background:     'var(--accent-dim)',
          border:         '1px solid rgba(99,102,241,0.3)',
          fontSize:       '12px',
          color:          'var(--accent-glow)',
          fontFamily:     'var(--font-mono)',
          marginBottom:   '24px',
        }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--success)', display: 'inline-block' }}/>
          Hybrid RAG · Cross-encoder Reranking · Langfuse Observability
        </div>

        <h1 style={{
          fontFamily:     'var(--font-display)',
          fontSize:       '42px',
          fontWeight:     700,
          letterSpacing:  '-0.04em',
          lineHeight:     1.1,
          marginBottom:   '16px',
          background:     'linear-gradient(135deg, var(--text-primary) 0%, var(--accent-glow) 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          Ask anything.<br/>Get cited answers.
        </h1>

        <p style={{
          color:    'var(--text-muted)',
          fontSize: '15px',
          maxWidth: '380px',
          margin:   '0 auto',
        }}>
          Upload a PDF. DocuMind AI parses, indexes, and answers your questions with exact page citations.
        </p>
      </div>

      {/* Drop zone */}
      <div {...getRootProps()} style={{
        padding:      '48px 32px',
        borderRadius: 'var(--radius-xl)',
        border:       `2px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`,
        textAlign:    'center',
        cursor:       uploading ? 'not-allowed' : 'pointer',
        transition:   'all 0.25s ease',
        background:   isDragActive ? 'var(--accent-dim)' : 'var(--bg-surface)',
        animation:    isDragActive ? 'glow-pulse 1.5s infinite' : 'none',
      }}>
        <input {...getInputProps()} />

        {uploading ? (
          <div style={{ animation: 'fade-in 0.3s ease' }}>
            <div style={{
              display:        'flex',
              justifyContent: 'center',
              gap:            '8px',
              marginBottom:   '16px',
            }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width:     '8px',
                  height:    '8px',
                  borderRadius: '50%',
                  background: 'var(--accent)',
                  animation: `pulse-dot 1.2s ease-in-out ${i * 0.2}s infinite`,
                }}/>
              ))}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--accent-glow)' }}>
              {progress}
            </div>
          </div>
        ) : (
          <>
            <div style={{ fontSize: '32px', marginBottom: '16px' }}>
              {isDragActive ? '📂' : '📄'}
            </div>
            <div style={{
              fontFamily:   'var(--font-display)',
              fontWeight:   600,
              fontSize:     '16px',
              color:        isDragActive ? 'var(--accent-glow)' : 'var(--text-primary)',
              marginBottom: '8px',
            }}>
              {isDragActive ? 'Drop it here' : 'Drop your PDF here'}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '20px' }}>
              or click to browse
            </div>
            <div style={{
              display:        'inline-flex',
              alignItems:     'center',
              gap:            '16px',
              padding:        '8px 16px',
              borderRadius:   'var(--radius-sm)',
              background:     'var(--bg-elevated)',
              fontSize:       '11px',
              color:          'var(--text-muted)',
              fontFamily:     'var(--font-mono)',
            }}>
              <span>PDF only</span>
              <span style={{ width: '1px', height: '12px', background: 'var(--border)' }}/>
              <span>Text · Tables · Images</span>
            </div>
          </>
        )}
      </div>

      {error && (
        <div style={{
          marginTop:    '16px',
          padding:      '12px 16px',
          borderRadius: 'var(--radius-md)',
          background:   'rgba(239,68,68,0.1)',
          border:       '1px solid rgba(239,68,68,0.3)',
          fontSize:     '13px',
          color:        'var(--error)',
        }}>{error}</div>
      )}
    </div>
  )
}