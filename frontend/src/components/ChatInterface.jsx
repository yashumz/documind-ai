import { useState, useRef, useEffect, forwardRef } from 'react'
import axios from 'axios'
import ThinkingState from './ThinkingState'
import AnswerCard    from './AnswerCard'

const API_BASE = '/api/v1'


const ChatInterface = forwardRef(function ChatInterface(
  { messages, setMessages, documentName },
  ref
) {
  const [question,  setQuestion]  = useState('')
  const [thinking,  setThinking]  = useState(null)  // null | 'search' | 'rerank' | 'generate'
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef  = useRef(null)
  const inputRef   = useRef(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  const handleSubmit = async (e) => {
    e?.preventDefault()
    if (!question.trim() || isLoading) return

    const userQuestion = question.trim()
    setQuestion('')
    setIsLoading(true)

    // Add user message
    setMessages(prev => [...prev, {
      id:   Date.now(),
      role: 'user',
      text: userQuestion,
    }])

    try {
      // Animate through pipeline stages
      setThinking('search')
      await delay(900)
      setThinking('rerank')
      await delay(800)
      setThinking('generate')

      const response = await axios.post(`${API_BASE}/query`, {
        question: userQuestion,
        source:   documentName,
      })

      setThinking(null)

      setMessages(prev => [...prev, {
        id:   Date.now() + 1,
        role: 'assistant',
        text: response.data.answer,
        meta: {
          sources:     response.data.sources_used,
          cost_usd:    response.data.cost_usd,
          chunks_used: response.data.chunks_used,
          model:       response.data.model,
        },
      }])

    } catch (err) {
      setThinking(null)
      setMessages(prev => [...prev, {
        id:   Date.now() + 1,
        role: 'error',
        text: err.response?.data?.detail || 'Something went wrong. Please try again.',
      }])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div style={{
      display:        'flex',
      flexDirection:  'column',
      height:         '100%',
      overflow:       'hidden',
    }}>

      {/* ── Message list ──────────────────────────────────── */}
      <div style={{
        flex:       1,
        overflowY:  'auto',
        padding:    '24px',
        display:    'flex',
        flexDirection: 'column',
        gap:        '16px',
      }}>

        {/* Welcome message */}
        {messages.length === 0 && (
          <div style={{
            textAlign:  'center',
            padding:    '60px 20px',
            color:      'var(--text-muted)',
            animation:  'fade-in 0.5s ease',
          }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>💬</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '8px' }}>
              Ask your first question
            </div>
            <div style={{ fontSize: '13px' }}>
              Try: "Summarise this document" or "What are the key findings?"
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} style={{ animation: 'fade-in 0.3s ease' }}>

            {/* System message */}
            {msg.role === 'system' && (
              <div style={{
                display:      'flex',
                alignItems:   'center',
                gap:          '8px',
                padding:      '10px 14px',
                borderRadius: 'var(--radius-md)',
                background:   'rgba(16,185,129,0.08)',
                border:       '1px solid rgba(16,185,129,0.2)',
              }}>
                <span style={{ color: 'var(--success)', fontSize: '12px' }}>✓</span>
                <span style={{ fontSize: '12px', color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>
                  {msg.text}
                </span>
                {msg.meta && (
                  <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
                    {[
                      { v: msg.meta.text,   l: 'text',   c: 'var(--accent-glow)' },
                      { v: msg.meta.tables, l: 'tables', c: 'var(--warning)' },
                      { v: msg.meta.images, l: 'images', c: '#EC4899' },
                    ].map(s => (
                      <span key={s.l} style={{
                        fontSize:   '11px',
                        fontFamily: 'var(--font-mono)',
                        color:      s.c,
                      }}>{s.v} {s.l}</span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* User message */}
            {msg.role === 'user' && (
              <div style={{
                display:   'flex',
                justifyContent: 'flex-end',
              }}>
                <div style={{
                  maxWidth:     '70%',
                  padding:      '12px 16px',
                  borderRadius: 'var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg)',
                  background:   'var(--accent)',
                  fontSize:     '14px',
                  lineHeight:   1.6,
                  color:        'white',
                  fontWeight:   450,
                }}>{msg.text}</div>
              </div>
            )}

            {/* Assistant answer */}
            {msg.role === 'assistant' && (
              <AnswerCard message={msg} />
            )}

            {/* Error */}
            {msg.role === 'error' && (
              <div style={{
                padding:      '12px 16px',
                borderRadius: 'var(--radius-md)',
                background:   'rgba(239,68,68,0.08)',
                border:       '1px solid rgba(239,68,68,0.2)',
                fontSize:     '13px',
                color:        'var(--error)',
              }}>{msg.text}</div>
            )}
          </div>
        ))}

        {/* Thinking state */}
        {thinking && (
          <ThinkingState stage={thinking} />
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ─────────────────────────────────────── */}
      <div style={{
        borderTop:  '1px solid var(--border)',
        padding:    '16px 24px',
        background: 'var(--bg-surface)',
      }}>
        <form onSubmit={handleSubmit} style={{
          display:      'flex',
          gap:          '12px',
          alignItems:   'flex-end',
        }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <textarea
              ref={inputRef}
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your document..."
              disabled={isLoading}
              rows={1}
              style={{
                width:        '100%',
                padding:      '12px 16px',
                borderRadius: 'var(--radius-md)',
                border:       `1px solid ${question ? 'var(--accent)' : 'var(--border)'}`,
                background:   'var(--bg-elevated)',
                color:        'var(--text-primary)',
                fontFamily:   'var(--font-body)',
                fontSize:     '14px',
                resize:       'none',
                outline:      'none',
                lineHeight:   1.6,
                transition:   'border-color 0.2s ease',
                minHeight:    '44px',
                maxHeight:    '120px',
              }}
            />
            <div style={{
              position:   'absolute',
              bottom:     '8px',
              right:      '12px',
              fontSize:   '11px',
              color:      'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              pointerEvents: 'none',
            }}>↵ send</div>
          </div>

          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            style={{
              padding:      '12px 20px',
              borderRadius: 'var(--radius-md)',
              border:       'none',
              background:   (!question.trim() || isLoading) ? 'var(--bg-elevated)' : 'var(--accent)',
              color:        (!question.trim() || isLoading) ? 'var(--text-muted)' : 'white',
              fontFamily:   'var(--font-display)',
              fontWeight:   600,
              fontSize:     '14px',
              cursor:       (!question.trim() || isLoading) ? 'not-allowed' : 'pointer',
              transition:   'all 0.2s ease',
              whiteSpace:   'nowrap',
              height:       '44px',
            }}
          >
            {isLoading ? '...' : 'Ask →'}
          </button>
        </form>
      </div>
    </div>
  )
})

const delay = ms => new Promise(r => setTimeout(r, ms))
export default ChatInterface