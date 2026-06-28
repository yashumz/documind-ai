export default function AnswerCard({ message }) {
    const { text, meta } = message
  
    return (
      <div style={{
        padding:      '20px 24px',
        borderRadius: 'var(--radius-lg)',
        background:   'var(--bg-surface)',
        border:       '1px solid var(--border)',
        animation:    'fade-in 0.4s ease',
      }}>
        {/* Answer text */}
        <div style={{
          fontSize:   '14px',
          lineHeight: 1.75,
          color:      'var(--text-primary)',
          whiteSpace: 'pre-wrap',
          marginBottom: meta ? '20px' : 0,
        }}>{text}</div>
  
        {/* Metadata row */}
        {meta && (
          <div style={{
            display:       'flex',
            alignItems:    'center',
            gap:           '16px',
            paddingTop:    '16px',
            borderTop:     '1px solid var(--border)',
            flexWrap:      'wrap',
          }}>
  
            {/* Sources */}
            {meta.sources?.length > 0 && (
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', flex: 1 }}>
                {meta.sources.map(([src, page], i) => (
                  <span key={i} style={{
                    padding:      '3px 10px',
                    borderRadius: 'var(--radius-sm)',
                    background:   'var(--accent-dim)',
                    border:       '1px solid rgba(99,102,241,0.3)',
                    fontSize:     '11px',
                    fontFamily:   'var(--font-mono)',
                    color:        'var(--accent-glow)',
                  }}>
                    {src} · p{page}
                  </span>
                ))}
              </div>
            )}
  
            {/* Cost + tokens */}
            <div style={{
              display:    'flex',
              gap:        '12px',
              flexShrink: 0,
            }}>
              {[
                { label: 'Cost',   value: `$${meta.cost_usd?.toFixed(4)}` },
                { label: 'Tokens', value: meta.chunks_used ? `${meta.chunks_used} chunks` : null },
                { label: 'Model',  value: meta.model?.replace('claude-', '') },
              ].filter(m => m.value).map(m => (
                <div key={m.label} style={{ textAlign: 'right' }}>
                  <div style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize:   '12px',
                    fontWeight: 500,
                    color:      'var(--text-primary)',
                  }}>{m.value}</div>
                  <div style={{
                    fontSize:   '10px',
                    color:      'var(--text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}>{m.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }