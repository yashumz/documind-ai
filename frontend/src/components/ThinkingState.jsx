const STAGES = [
    { id: 'search',   label: 'Hybrid search',    detail: 'BM25 + dense retrieval' },
    { id: 'rerank',   label: 'Reranking',         detail: 'Cross-encoder scoring' },
    { id: 'generate', label: 'Generating answer', detail: 'Claude Sonnet' },
  ]
  
  export default function ThinkingState({ stage }) {
    const currentIdx = STAGES.findIndex(s => s.id === stage)
  
    return (
      <div style={{
        padding:      '20px 24px',
        borderRadius: 'var(--radius-lg)',
        background:   'var(--bg-surface)',
        border:       '1px solid var(--border)',
        animation:    'fade-in 0.3s ease',
      }}>
        <div style={{
          fontSize:     '11px',
          color:        'var(--text-muted)',
          fontFamily:   'var(--font-mono)',
          marginBottom: '16px',
          letterSpacing: '0.08em',
        }}>PROCESSING</div>
  
        {STAGES.map((s, i) => {
          const isDone    = i < currentIdx
          const isActive  = i === currentIdx
          const isPending = i > currentIdx
  
          return (
            <div key={s.id} style={{
              display:      'flex',
              alignItems:   'center',
              gap:          '12px',
              padding:      '10px 0',
              borderBottom: i < STAGES.length - 1 ? '1px solid var(--border)' : 'none',
              opacity:      isPending ? 0.3 : 1,
              transition:   'opacity 0.3s ease',
            }}>
              {/* Stage indicator */}
              <div style={{
                width:          '28px',
                height:         '28px',
                borderRadius:   '50%',
                flexShrink:     0,
                display:        'flex',
                alignItems:     'center',
                justifyContent: 'center',
                background:     isDone    ? 'var(--success)'  :
                                isActive  ? 'var(--accent)'   : 'var(--bg-elevated)',
                border:         isActive  ? '2px solid var(--accent-glow)' : '2px solid transparent',
                fontSize:       '12px',
                transition:     'all 0.3s ease',
              }}>
                {isDone ? '✓' : isActive ? (
                  <div style={{
                    width:  '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: 'white',
                    animation: 'pulse-dot 1s ease-in-out infinite',
                  }}/>
                ) : <span style={{ color: 'var(--text-subtle)' }}>{i + 1}</span>}
              </div>
  
              {/* Stage info */}
              <div>
                <div style={{
                  fontSize:   '13px',
                  fontWeight: 500,
                  color:      isActive ? 'var(--text-primary)' : isDone ? 'var(--success)' : 'var(--text-muted)',
                }}>{s.label}</div>
                <div style={{
                  fontSize:   '11px',
                  color:      'var(--text-muted)',
                  fontFamily: 'var(--font-mono)',
                }}>{s.detail}</div>
              </div>
  
              {/* Active spinner */}
              {isActive && (
                <div style={{
                  marginLeft: 'auto',
                  display:    'flex',
                  gap:        '4px',
                }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{
                      width:     '4px',
                      height:    '4px',
                      borderRadius: '50%',
                      background: 'var(--accent)',
                      animation: `pulse-dot 1.2s ease ${i * 0.15}s infinite`,
                    }}/>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }