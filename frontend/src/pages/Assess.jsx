import { useState } from 'react'

const LEVELS = {
  LOW:      { color:'var(--green)',  cls:'card-green',  tag:'tag-green' },
  MEDIUM:   { color:'var(--amber)',  cls:'card-amber',  tag:'tag-amber' },
  HIGH:     { color:'var(--amber)',  cls:'card-amber',  tag:'tag-amber' },
  CRITICAL: { color:'var(--red)',    cls:'card-red',    tag:'tag-red'   },
}

const EXAMPLES = [
  "I found what appears to be an AI-generated explicit image of me being shared in a private Telegram group. My face is recognisable but the body is not mine.",
  "A post on Reddit containing a deepfake of my face has 500+ upvotes. I have no idea how far it has spread.",
  "I received an anonymous message threatening to distribute a synthetic intimate image of me to my employer unless I pay £5,000.",
]

export default function Assess() {
  const [desc, setDesc]       = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)

  async function assess() {
    setLoading(true); setError(null)
    try {
      const res  = await fetch('/api/assess', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({description:desc}) })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Assessment failed')
      setResult(data)
    } catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const lc = result ? (LEVELS[result.threat_level] || LEVELS.MEDIUM) : null

  return (
    <main style={{ padding:'40px 0 72px' }}>
      <div className="wrap">

        <div className="a1" style={{ marginBottom:32 }}>
          <div className="label" style={{ marginBottom:10 }}>Threat Intelligence Module</div>
          <h2 style={{ marginBottom:8 }}>Situation Assessment</h2>
          <p style={{ fontSize:14, maxWidth:560 }}>
            Describe your situation. The local LLM evaluates threat level, assesses spread risk,
            and generates a prioritised action protocol with relevant legal options.
          </p>
        </div>

        <div className="grid-2" style={{ gap:24, alignItems:'start' }}>

          {/* Input */}
          <div className="a2">
            <div className="card" style={{ marginBottom:16 }}>
              <div className="input-label">Situation Description</div>
              <textarea className="input" rows={7}
                placeholder="Describe what happened. Include the platform where you found the content, estimated audience size, when it was posted, and any contact you have received..."
                value={desc} onChange={e => setDesc(e.target.value)} />
              <button className="btn btn-primary btn-md" onClick={assess}
                disabled={loading || !desc.trim()} style={{ width:'100%', marginTop:14 }}>
                {loading
                  ? <><div className="spinner" style={{ width:15,height:15,borderWidth:2 }} /> Assessing Threat Level...</>
                  : 'Assess Threat Level — Generate Action Protocol'}
              </button>
              {error && <div className="err" style={{ marginTop:12 }}>{error}</div>}
            </div>

            <div className="card">
              <div className="mono muted" style={{ marginBottom:14, fontSize:9 }}>EXAMPLE SITUATIONS</div>
              {EXAMPLES.map((ex, i) => (
                <div key={i} onClick={() => setDesc(ex)}
                  style={{
                    padding:'12px 14px', borderRadius:6, cursor:'pointer',
                    background:'var(--bg2)', border:'1px solid var(--line)',
                    marginBottom: i < EXAMPLES.length-1 ? 10 : 0,
                    fontSize:13, color:'var(--text-dim)', lineHeight:1.6,
                    transition:'all .2s',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor='rgba(255,255,255,.15)'; e.currentTarget.style.color='var(--text)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor='var(--line)'; e.currentTarget.style.color='var(--text-dim)' }}>
                  <div className="mono" style={{ color:'var(--cyan)', marginBottom:5, fontSize:9 }}>EXAMPLE {i+1} — CLICK TO USE</div>
                  {ex}
                </div>
              ))}
            </div>
          </div>

          {/* Results */}
          <div className="a3">
            {!result && !loading && (
              <div className="card" style={{ padding:'64px 24px', textAlign:'center' }}>
                <div style={{ fontFamily:'var(--font-serif)', fontSize:64, fontWeight:700, opacity:.04, color:'var(--cyan)', marginBottom:14 }}>?</div>
                <p className="mono muted">AWAITING SITUATION INPUT</p>
              </div>
            )}

            {loading && (
              <div className="card" style={{ padding:'48px 24px', textAlign:'center' }}>
                <div className="spinner" style={{ width:40, height:40, margin:'0 auto 20px' }} />
                <p className="mono" style={{ color:'var(--cyan)', fontSize:11 }}>Local LLM processing your situation...</p>
              </div>
            )}

            {result && lc && (
              <div className="a1">
                {/* Threat level */}
                <div className={`card ${lc.cls}`} style={{ marginBottom:14, textAlign:'center', padding:24 }}>
                  <div className="mono muted" style={{ marginBottom:8, fontSize:9 }}>THREAT LEVEL</div>
                  <div style={{ fontFamily:'var(--font-serif)', fontSize:36, fontWeight:700, color:lc.color, textShadow:`0 0 30px ${lc.color}50` }}>
                    {result.threat_level}
                  </div>
                  {result.urgency_score && (
                    <div className="mono muted" style={{ marginTop:8, fontSize:10 }}>
                      URGENCY SCORE: {result.urgency_score}/10
                    </div>
                  )}
                </div>

                {/* Spread risk */}
                {result.estimated_spread_risk && (
                  <div className="card" style={{ marginBottom:14, display:'flex', gap:14, alignItems:'center' }}>
                    <div>
                      <div className="mono muted" style={{ marginBottom:4, fontSize:9 }}>ESTIMATED SPREAD RISK</div>
                      <span className={`tag ${result.estimated_spread_risk === 'HIGH' || result.estimated_spread_risk === 'CRITICAL' ? 'tag-red' : result.estimated_spread_risk === 'MEDIUM' ? 'tag-amber' : 'tag-green'}`}>
                        {result.estimated_spread_risk}
                      </span>
                    </div>
                    <div style={{ flex:1 }}>
                      <div className="progress">
                        <div className={`progress-bar ${result.threat_level === 'CRITICAL' || result.threat_level === 'HIGH' ? 'red' : 'amber'}`}
                          style={{ width: result.threat_level === 'CRITICAL' ? '90%' : result.threat_level === 'HIGH' ? '70%' : result.threat_level === 'MEDIUM' ? '45%' : '20%' }} />
                      </div>
                    </div>
                  </div>
                )}

                {/* Support message */}
                {result.support_message && (
                  <div className="card card-cyan" style={{ marginBottom:14 }}>
                    <blockquote style={{ border:'none', background:'none', padding:0 }}>
                      {result.support_message}
                    </blockquote>
                  </div>
                )}

                {/* Immediate steps */}
                {result.immediate_steps && (
                  <div className="card card-red" style={{ marginBottom:14 }}>
                    <div className="mono" style={{ color:'var(--red)', marginBottom:12, fontSize:9 }}>IMMEDIATE ACTION PROTOCOL</div>
                    {result.immediate_steps.map((s, i) => (
                      <div key={i} style={{ display:'flex', gap:12, marginBottom:10, alignItems:'flex-start' }}>
                        <span className="mono" style={{ color:'var(--red)', background:'rgba(255,68,68,.1)', padding:'2px 7px', borderRadius:3, flexShrink:0, fontSize:10 }}>
                          {String(i+1).padStart(2,'0')}
                        </span>
                        <span style={{ fontSize:13, color:'var(--text-dim)', lineHeight:1.55 }}>{s}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Legal options */}
                {result.legal_options && (
                  <div className="card" style={{ marginBottom:14 }}>
                    <div className="mono muted" style={{ marginBottom:12, fontSize:9 }}>APPLICABLE LEGAL FRAMEWORKS</div>
                    {result.legal_options.map((o, i) => (
                      <div key={i} style={{ display:'flex', gap:10, marginBottom:8, alignItems:'flex-start' }}>
                        <span style={{ color:'var(--cyan)', flexShrink:0 }}>◈</span>
                        <span style={{ fontSize:13, color:'var(--text-dim)', lineHeight:1.55 }}>{o}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Next steps */}
                <div style={{ display:'flex', gap:10, flexWrap:'wrap' }}>
                  <a href="/scan" className="btn btn-primary btn-sm" style={{ flex:1 }}>Scan Image for Leaks</a>
                  <a href="/legal" className="btn btn-outline btn-sm" style={{ flex:1 }}>Generate Legal Docs</a>
                  <a href="https://cybercivilrights.org/ccri-crisis-helpline/" target="_blank" rel="noopener noreferrer"
                    className="btn btn-ghost btn-sm" style={{ flex:1 }}>CCRI Crisis Line</a>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
