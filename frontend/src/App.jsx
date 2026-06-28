import { useState, useRef } from 'react'
import UploadZone   from './components/UploadZone'
import ChatInterface from './components/ChatInterface'

export default function App() {
  const [uploadedDoc, setUploadedDoc] = useState(null)
  const [messages,    setMessages]    = useState([])
  const chatRef = useRef(null)

  const handleUploadSuccess = (docInfo) => {
    setUploadedDoc(docInfo)
    // Add a system message to chat
    setMessages([{
      id:   Date.now(),
      role: 'system',
      text: `Document ready: ${docInfo.filename} — ${docInfo.total_chunks} chunks indexed`,
      meta: {
        chunks:  docInfo.total_chunks,
        text:    docInfo.text_chunks,
        tables:  docInfo.table_chunks,
        images:  docInfo.image_chunks,
      }
    }])
  }

  return (
    <div style={{
      display:       'grid',
      gridTemplateColumns: uploadedDoc ? '380px 1fr' : '1fr',
      gridTemplateRows:    '56px 1fr',
      height:        '100vh',
      overflow:      'hidden',
      transition:    'grid-template-columns 0.4s ease',
    }}>

      {/* ── Top nav ──────────────────────────────────────── */}
      <header style={{
        gridColumn:     '1 / -1',
        display:        'flex',
        alignItems:     'center',
        gap:            '12px',
        padding:        '0 24px',
        borderBottom:   '1px solid var(--border)',
        background:     'var(--bg-surface)',
      }}>
        {/* Logo mark */}
        <div style={{
          width:        '28px',
          height:       '28px',
          borderRadius: '8px',
          background:   'var(--accent)',
          display:      'flex',
          alignItems:   'center',
          justifyContent: 'center',
          fontSize:     '14px',
          fontWeight:   700,
          fontFamily:   'var(--font-display)',
        }}>D</div>

        <span style={{
          fontFamily: 'var(--font-display)',
          fontWeight: 600,
          fontSize:   '15px',
          letterSpacing: '-0.02em',
        }}>DocuMind AI</span>

        <span style={{
          fontSize:   '11px',
          color:      'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          marginLeft: '4px',
        }}>v1.0</span>

        {/* Status indicator */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{
            width: '6px', height: '6px',
            borderRadius: '50%',
            background: 'var(--success)',
            boxShadow: '0 0 6px var(--success)',
          }}/>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {uploadedDoc ? `${uploadedDoc.filename}` : 'No document loaded'}
          </span>
        </div>
      </header>

      {/* ── Left panel: upload ────────────────────────────── */}
      <aside style={{
        borderRight:  '1px solid var(--border)',
        overflowY:    'auto',
        background:   'var(--bg-surface)',
        display:      uploadedDoc ? 'block' : 'none',
      }}>
        <UploadZone
          onSuccess={handleUploadSuccess}
          currentDoc={uploadedDoc}
        />
      </aside>

      {/* ── Main area ─────────────────────────────────────── */}
      <main style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {!uploadedDoc ? (
          /* Centre the upload zone when no doc */
          <div style={{
            flex:           1,
            display:        'flex',
            alignItems:     'center',
            justifyContent: 'center',
            padding:        '40px',
          }}>
            <UploadZone onSuccess={handleUploadSuccess} currentDoc={null} />
          </div>
        ) : (
          <ChatInterface
            ref={chatRef}
            messages={messages}
            setMessages={setMessages}
            documentName={uploadedDoc.filename}
          />
        )}
      </main>
    </div>
  )
}