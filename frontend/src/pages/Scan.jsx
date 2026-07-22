import { useState, useRef } from 'react'

/* ── Verdict config (3-class internal: Real / AI Generated / Deepfake) ── */
const VERDICT = {
  // Primary 3-class labels from ensemble
  'Real':         { color:'var(--green)',  cls:'card-green',  tag:'tag-green',  label:'REAL',          sub:'Authentic photograph — no AI synthesis indicators detected' },
  'AI Generated': { color:'var(--amber)',  cls:'card-amber',  tag:'tag-amber',  label:'AI GENERATED',  sub:'Full-scene AI/synthetic image detected (Stable Diffusion, DALL-E, etc.)' },
  'Deepfake':     { color:'var(--red)',    cls:'card-red',    tag:'tag-red',    label:'DEEPFAKE',      sub:'Face-swap or face-manipulation on a real image — deepfake confirmed' },
  // Legacy fallbacks (backward compat)
  SAFE:           { color:'var(--green)',  cls:'card-green',  tag:'tag-green',  label:'AUTHENTIC',        sub:'No AI synthesis indicators detected' },
  SUSPICIOUS:     { color:'var(--amber)',  cls:'card-amber',  tag:'tag-amber',  label:'INCONCLUSIVE',     sub:'Borderline — manual review advised' },
  LIKELY_FAKE:    { color:'var(--amber)',  cls:'card-amber',  tag:'tag-amber',  label:'LIKELY SYNTHETIC', sub:'Strong AI generation indicators present' },
  CONFIRMED_FAKE: { color:'var(--red)',    cls:'card-red',    tag:'tag-red',    label:'CONFIRMED FAKE',   sub:'High-confidence AI-generated content' },
  Authentic:      { color:'var(--green)',  cls:'card-green',  tag:'tag-green',  label:'AUTHENTIC',        sub:'No AI synthesis indicators detected' },
  Suspicious:     { color:'var(--amber)',  cls:'card-amber',  tag:'tag-amber',  label:'INCONCLUSIVE',     sub:'Borderline — manual review advised' },
}
const THREAT_COLOR = { CRITICAL:'var(--red)', HIGH:'rgba(255,110,60,.9)', MEDIUM:'var(--amber)', LOW:'var(--green)', NONE:'var(--green)' }
const THREAT_TAG   = { CRITICAL:'tag-red', HIGH:'tag-red', MEDIUM:'tag-amber', LOW:'tag-green', NONE:'tag-green' }
const SEV_COLOR    = { CRITICAL:'var(--red)', HIGH:'rgba(255,110,60,.9)', MEDIUM:'var(--amber)', LOW:'var(--green)' }

function NSFWPanel({ nsfw }) {
  if (!nsfw || nsfw.category === 'UNKNOWN') return null
  const isExplicit = nsfw.is_explicit
  const level      = nsfw.level || 'NONE'
  const color      = THREAT_COLOR[level] || 'var(--green)'
  const score      = Math.round((nsfw.nsfw_score || 0) * 100)
  const categoryLabel = {
    EXPLICIT:'AI-Generated Explicit / Nude', SUGGESTIVE:'Suggestive / Borderline NSFW',
    AI_HENTAI:'AI-Generated Explicit Illustration', DRAWING:'Illustrated / Non-Photographic', SAFE:'Safe Content',
  }[nsfw.category] || nsfw.category
  return (
    <div className={`card ${isExplicit ? 'card-red' : level === 'MEDIUM' ? 'card-amber' : 'card-green'}`} style={{ marginBottom:14 }}>
      <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:12, flexWrap:'wrap' }}>
        <div className="mono" style={{ color, fontSize:9, letterSpacing:'.1em' }}>NSFW / EXPLICIT CONTENT ANALYSIS</div>
        {isExplicit && <span className="tag tag-red" style={{ marginLeft:'auto' }}>EXPLICIT DETECTED</span>}
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:8, marginBottom:14 }}>
        {[
          { l:'NSFW SCORE', v:`${score}%`, c:color },
          { l:'EXPLICIT',   v:`${Math.round((nsfw.explicit_score||0)*100)}%`, c:'var(--red)' },
          { l:'SAFE',       v:`${Math.round((nsfw.safe_score||0)*100)}%`,     c:'var(--green)' },
        ].map(m => (
          <div key={m.l} style={{ textAlign:'center', background:'var(--bg2)', borderRadius:6, padding:'10px 8px', border:'1px solid var(--line)' }}>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:20, fontWeight:700, color:m.c }}>{m.v}</div>
            <div className="mono muted" style={{ marginTop:3, fontSize:9 }}>{m.l}</div>
          </div>
        ))}
      </div>
      <div style={{ marginBottom:10 }}>
        <div style={{ display:'flex', justifyContent:'space-between', marginBottom:5 }}>
          <span className="mono muted" style={{ fontSize:9 }}>EXPLICIT PROBABILITY</span>
          <span className="mono" style={{ fontSize:9, color }}>{score}%</span>
        </div>
        <div className="progress">
          <div className={`progress-bar ${score > 60 ? 'red' : score > 35 ? 'amber' : ''}`} style={{ width:`${score}%` }} />
        </div>
      </div>
      <div style={{ background:'var(--bg2)', borderRadius:6, padding:'10px 14px', marginBottom:12, border:'1px solid var(--line)' }}>
        <div className="mono muted" style={{ marginBottom:4, fontSize:9 }}>CLASSIFICATION</div>
        <div style={{ fontFamily:'var(--font-serif)', fontSize:14, fontWeight:700, color }}>{categoryLabel}</div>
      </div>
      {nsfw.flags && nsfw.flags.length > 0 && (
        <div>
          <div className="mono muted" style={{ marginBottom:8, fontSize:9 }}>DETECTION FLAGS</div>
          {nsfw.flags.map((f, i) => (
            <div key={i} style={{ display:'flex', gap:8, marginBottom:6, fontSize:12, color:'var(--text-dim)', lineHeight:1.5, alignItems:'flex-start' }}>
              <span style={{ color, flexShrink:0, marginTop:1 }}>◈</span> {f}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PoliceComplaintPanel({ complaint, result }) {
  const [open,       setOpen]       = useState(false)
  const [copied,     setCopied]     = useState(false)
  const [aiText,     setAiText]     = useState('')       // streamed LLM output
  const [generating, setGenerating] = useState(false)
  const [generated,  setGenerated]  = useState(false)
  const [genError,   setGenError]   = useState('')
  const textRef = useRef(null)

  // STRICT GUARD — only render for confirmed Deepfakes
  if (!complaint || !complaint.generated) return null

  // ── Copy template or AI text ───────────────────────────────────────────
  function copyText() {
    const text = aiText || complaint.complaint_text || ''
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 2000)
    })
  }

  // ── Stream AI complaint from /api/complaint/generate ──────────────────
  async function generateAiComplaint() {
    setGenerating(true); setGenError(''); setAiText(''); setGenerated(false)
    try {
      const res = await fetch('/api/complaint/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          classification: result?.classification || 'Deepfake',
          filename:       result?.filename       || 'uploaded_image',
          confidence:     result?.confidence     || complaint.confidence || 0,
          risk_score:     result?.risk_score     || complaint.risk_score || 0,
          indicators:     result?.indicators     || [],
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      const reader = res.body.getReader()
      const dec    = new TextDecoder()
      let full = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = dec.decode(value, { stream: true })
        full += chunk
        setAiText(full)
        // Auto-scroll textarea
        if (textRef.current) textRef.current.scrollTop = textRef.current.scrollHeight
      }
      setGenerated(true)
    } catch (e) {
      setGenError(e.message || 'Generation failed — ensure Ollama is running (ollama serve)')
    } finally {
      setGenerating(false)
    }
  }

  // ── Gmail deep link ────────────────────────────────────────────────────
  function openGmail() {
    const body     = aiText || complaint.complaint_text || ''
    const subject  = 'URGENT: Deepfake Content Complaint – Request for Investigation'
    const gmailUrl =
      `https://mail.google.com/mail/?view=cm&fs=1` +
      `&to=cybercrime%40india.gov.in` +
      `&su=${encodeURIComponent(subject)}` +
      `&body=${encodeURIComponent(body)}`
    window.open(gmailUrl, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="card card-red" style={{ marginBottom:14, border:'2px solid rgba(255,68,68,.4)' }}>
      {/* Header */}
      <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:14, flexWrap:'wrap' }}>
        <div style={{ width:44, height:44, borderRadius:10, background:'rgba(255,68,68,.12)', border:'1px solid rgba(255,68,68,.3)', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
          <span style={{ fontSize:20 }}>🚨</span>
        </div>
        <div style={{ flex:1 }}>
          <div className="mono" style={{ color:'var(--red)', fontSize:9, letterSpacing:'.1em', marginBottom:4 }}>CYBERCRIME POLICE COMPLAINT — INDIA</div>
          <div style={{ fontFamily:'var(--font-serif)', fontSize:15, fontWeight:700 }}>Deepfake Confirmed — File Police Report Now</div>
        </div>
        <span className="tag tag-red">DEEPFAKE VERIFIED</span>
      </div>

      {/* Emergency numbers */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:8, marginBottom:14 }}>
        {[
          { num:'112',  label:'National Emergency', desc:'Dial 112 for police, fire, ambulance — 24/7' },
          { num:'1930', label:'Cybercrime Helpline', desc:'Report deepfake abuse & NCII — 24/7' },
        ].map(h => (
          <div key={h.num} style={{ background:'rgba(255,68,68,.06)', borderRadius:8, padding:'12px 14px', border:'1px solid rgba(255,68,68,.2)' }}>
            <div style={{ fontFamily:'var(--font-mono)', fontSize:22, fontWeight:700, color:'var(--red)', marginBottom:4 }}>{h.num}</div>
            <div className="mono muted" style={{ fontSize:9, marginBottom:2 }}>{h.label}</div>
            <div style={{ fontSize:11, color:'var(--text-dim)', lineHeight:1.4 }}>{h.desc}</div>
          </div>
        ))}
      </div>

      {/* Portal link */}
      <div style={{ background:'rgba(255,68,68,.04)', border:'1px solid rgba(255,68,68,.15)', borderRadius:6, padding:'10px 14px', marginBottom:14, display:'flex', alignItems:'center', gap:10 }}>
        <span style={{ fontSize:14 }}>🌐</span>
        <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer"
          style={{ color:'var(--red)', fontFamily:'var(--font-mono)', fontSize:11, textDecoration:'none' }}>
          https://cybercrime.gov.in
        </a>
        <span style={{ fontSize:11, color:'var(--text-dim)', marginLeft:6 }}>— Official National Cybercrime Reporting Portal</span>
      </div>

      {/* Immediate steps */}
      {complaint.immediate_steps && (
        <div style={{ marginBottom:14 }}>
          <div className="mono" style={{ color:'var(--red)', marginBottom:10, fontSize:9 }}>IMMEDIATE STEPS</div>
          {complaint.immediate_steps.map((s, i) => (
            <div key={i} style={{ display:'flex', gap:10, marginBottom:8, fontSize:13, color:'var(--text-dim)', lineHeight:1.55 }}>
              <span style={{ color:'var(--red)', flexShrink:0, marginTop:1 }}>▸</span> {s}
            </div>
          ))}
        </div>
      )}

      {/* ── AI Generate section ──────────────────────────────────────────── */}
      <div style={{ borderTop:'1px solid rgba(255,68,68,.2)', paddingTop:14, marginTop:2 }}>
        <div className="mono" style={{ color:'var(--red)', fontSize:9, marginBottom:10 }}>AI-GENERATED POLICE COMPLAINT (OLLAMA)</div>

        {/* Generate button */}
        <button
          onClick={generateAiComplaint}
          disabled={generating}
          className="btn btn-danger btn-sm"
          style={{ width:'100%', marginBottom:12, fontSize:11, position:'relative', overflow:'hidden' }}
        >
          {generating
            ? <><div className="spinner" style={{ width:13, height:13, borderWidth:2, display:'inline-block', marginRight:8, verticalAlign:'middle' }} />Generating complaint via Ollama…</>
            : generated ? '↻ Regenerate Police Report' : '⚖ Generate Police Report'}
        </button>

        {/* Error */}
        {genError && (
          <div style={{ background:'rgba(255,68,68,.08)', border:'1px solid rgba(255,68,68,.25)', borderRadius:6, padding:'10px 14px', marginBottom:12, fontSize:12, color:'var(--red)', lineHeight:1.5 }}>
            ⚠ {genError}
          </div>
        )}

        {/* Streaming / generated text */}
        {(aiText || generating) && (
          <div style={{ marginBottom:12 }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:6 }}>
              <span className="mono muted" style={{ fontSize:9 }}>
                {generating ? '⟳ STREAMING FROM OLLAMA…' : '✓ COMPLAINT READY — REVIEW BEFORE SENDING'}
              </span>
              {aiText && (
                <button onClick={copyText} className="btn btn-ghost btn-sm" style={{ fontSize:9 }}>
                  {copied ? '✓ COPIED' : 'COPY'}
                </button>
              )}
            </div>
            <textarea
              ref={textRef}
              readOnly
              value={aiText}
              style={{
                width:'100%', minHeight:260, maxHeight:380, resize:'vertical',
                fontFamily:'var(--font-mono)', fontSize:11, color:'var(--text-dim)',
                background:'var(--bg2)', border:'1px solid rgba(255,68,68,.25)',
                borderRadius:6, padding:12, lineHeight:1.7, boxSizing:'border-box',
              }}
            />
            {generating && (
              <div className="mono muted" style={{ fontSize:9, marginTop:4, textAlign:'right' }}>
                {aiText.length} chars…
              </div>
            )}
          </div>
        )}

        {/* Template accordion (fallback) */}
        {!aiText && !generating && (
          <>
            <button onClick={() => setOpen(o => !o)}
              style={{ width:'100%', display:'flex', justifyContent:'space-between', alignItems:'center', background:'rgba(255,68,68,.06)', border:'1px solid rgba(255,68,68,.15)', borderRadius:6, padding:'10px 14px', cursor:'pointer', marginBottom: open ? 10 : 0 }}>
              <span className="mono" style={{ color:'var(--red)', fontSize:9 }}>VIEW TEMPLATE (Fill in your details)</span>
              <span style={{ color:'var(--text-muted)', display:'inline-block', transform:open?'rotate(180deg)':'none', transition:'transform .2s' }}>▼</span>
            </button>
            {open && (
              <div style={{ background:'var(--bg2)', border:'1px solid var(--line)', borderRadius:6, padding:14, marginBottom:10 }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:10 }}>
                  <span className="mono muted" style={{ fontSize:9 }}>TEMPLATE — requires your personal details</span>
                  <button onClick={copyText} className="btn btn-ghost btn-sm" style={{ fontSize:9 }}>{copied ? '✓ COPIED' : 'COPY'}</button>
                </div>
                <pre style={{ fontFamily:'var(--font-mono)', fontSize:11, color:'var(--text-dim)', whiteSpace:'pre-wrap', lineHeight:1.7, maxHeight:300, overflowY:'auto' }}>
                  {complaint.complaint_text}
                </pre>
              </div>
            )}
          </>
        )}

        {/* Action buttons */}
        <div style={{ display:'flex', gap:8, flexWrap:'wrap', marginTop:8 }}>
          {/* Send to Police — only enabled once AI text is generated */}
          <button
            onClick={openGmail}
            disabled={!generated && !aiText}
            className="btn btn-danger btn-sm"
            title={(!generated && !aiText) ? 'Generate the complaint first' : 'Open Gmail with pre-filled complaint'}
            style={{ flex:'1 1 160px', opacity:(!generated && !aiText) ? 0.45 : 1, cursor:(!generated && !aiText) ? 'not-allowed' : 'pointer' }}
          >
            📧 Send to Police (Gmail)
          </button>
          <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer"
            className="btn btn-outline btn-sm" style={{ flex:'1 1 160px' }}>
            🌐 File at cybercrime.gov.in
          </a>
          <a href="https://cybercivilrights.org/ccri-crisis-helpline/" target="_blank" rel="noopener noreferrer"
            className="btn btn-ghost btn-sm" style={{ flex:'1 1 140px' }}>
            CCRI Crisis Support
          </a>
        </div>

        {/* Safety notice */}
        <div style={{ marginTop:12, fontSize:11, color:'var(--text-dim)', lineHeight:1.5, background:'rgba(255,68,68,.04)', border:'1px solid rgba(255,68,68,.1)', borderRadius:6, padding:'8px 12px' }}>
          ⚠ This AI-generated complaint is a starting point. Review all details, add your personal information, and consult a legal professional before formal submission.
        </div>
      </div>
    </div>
  )
}

function ThreatProfilePanel({ profile }) {
  const [tab, setTab] = useState('overview')
  if (!profile || !profile.label) return null
  const sevColor = SEV_COLOR[profile.severity] || 'var(--amber)'
  const isCritical = profile.severity === 'CRITICAL' || profile.severity === 'HIGH'
  return (
    <div className={`card ${isCritical ? 'card-red' : 'card-amber'}`} style={{ marginBottom:14 }}>
      <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:16, flexWrap:'wrap' }}>
        <div style={{ width:48, height:48, borderRadius:10, background:`${sevColor}12`, border:`1px solid ${sevColor}30`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
          <span className="mono" style={{ color:sevColor, fontSize:12, fontWeight:700 }}>{profile.threat_code}</span>
        </div>
        <div style={{ flex:1 }}>
          <div className="mono" style={{ color:sevColor, fontSize:9, letterSpacing:'.1em', marginBottom:4 }}>THREAT ACTOR PROFILE</div>
          <div style={{ fontFamily:'var(--font-serif)', fontSize:15, fontWeight:700, color:'var(--text)' }}>{profile.label}</div>
        </div>
        <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:6, flexShrink:0 }}>
          <span className={`tag ${profile.severity === 'CRITICAL' ? 'tag-red' : profile.severity === 'HIGH' ? 'tag-red' : profile.severity === 'MEDIUM' ? 'tag-amber' : 'tag-green'}`}>{profile.severity} THREAT</span>
          <span className="mono muted" style={{ fontSize:9 }}>CONFIDENCE: {profile.confidence}%</span>
        </div>
      </div>
      <div style={{ marginBottom:14 }}>
        <div className="progress" style={{ height:3 }}>
          <div className={`progress-bar ${profile.severity === 'CRITICAL' ? 'red' : 'amber'}`} style={{ width:`${profile.confidence}%` }} />
        </div>
      </div>
      {profile.evidence && profile.evidence.length > 0 && (
        <div style={{ marginBottom:14 }}>
          <div className="mono muted" style={{ marginBottom:8, fontSize:9 }}>EVIDENCE SIGNALS</div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
            {profile.evidence.map((e, i) => <span key={i} className="tag tag-muted" style={{ fontSize:9, color:'var(--text-dim)' }}>{e}</span>)}
          </div>
        </div>
      )}
      <div style={{ display:'flex', gap:2, borderBottom:'1px solid var(--line)', marginBottom:14 }}>
        {[{ id:'overview',label:'Overview' },{ id:'modus',label:'Methods' },{ id:'origin',label:'Origin' },{ id:'track',label:'Track & Report' },{ id:'law',label:'Legal' }].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ fontFamily:'var(--font-mono)', fontSize:9, letterSpacing:'.08em', textTransform:'uppercase', color:tab===t.id?sevColor:'var(--text-muted)', padding:'8px 12px', cursor:'pointer', background:'none', border:'none', borderBottom:`2px solid ${tab===t.id?sevColor:'transparent'}`, marginBottom:'-1px', transition:'all .2s' }}>{t.label}</button>
        ))}
      </div>
      <div style={{ fontSize:13, color:'var(--text-dim)', lineHeight:1.7 }}>
        {tab==='overview' && <p>{profile.description}</p>}
        {tab==='modus' && <div>{(profile.modus_operandi||[]).map((m,i) => <div key={i} style={{ display:'flex', gap:10, marginBottom:10, alignItems:'flex-start' }}><span style={{ color:sevColor, flexShrink:0, fontFamily:'var(--font-mono)', fontSize:10 }}>{String(i+1).padStart(2,'0')}</span>{m}</div>)}</div>}
        {tab==='origin' && <div><div className="mono muted" style={{ marginBottom:10, fontSize:9 }}>LIKELY ORIGIN SIGNALS</div>{(profile.likely_origin||[]).map((o,i) => <div key={i} style={{ display:'flex', gap:8, marginBottom:8, alignItems:'flex-start' }}><span style={{ color:'var(--cyan)', flexShrink:0 }}>›</span>{o}</div>)}</div>}
        {tab==='track' && <div><div className="mono muted" style={{ marginBottom:10, fontSize:9 }}>TRACKING & REPORTING TIPS</div>{(profile.tracking_tips||[]).map((t,i) => <div key={i} style={{ display:'flex', gap:10, marginBottom:10, alignItems:'flex-start' }}><span className="mono" style={{ color:sevColor, background:`${sevColor}10`, padding:'2px 7px', borderRadius:3, flexShrink:0, fontSize:10 }}>{String(i+1).padStart(2,'0')}</span>{t}</div>)}</div>}
        {tab==='law' && <div><div className="mono muted" style={{ marginBottom:10, fontSize:9 }}>APPLICABLE LEGAL FRAMEWORKS</div>{(profile.law_applicable||[]).map((l,i) => <div key={i} style={{ display:'flex', gap:8, marginBottom:8, alignItems:'flex-start' }}><span style={{ color:'var(--gold)', flexShrink:0 }}>§</span>{l}</div>)}</div>}
      </div>
      {profile.distribution_timeline && profile.distribution_timeline.length > 0 && (
        <div style={{ marginTop:14 }}>
          <div className="mono muted" style={{ marginBottom:10, fontSize:9 }}>DISTRIBUTION TIMELINE</div>
          <div style={{ position:'relative', paddingLeft:20 }}>
            <div style={{ position:'absolute', left:7, top:6, bottom:6, width:1, background:'var(--line2)' }} />
            {profile.distribution_timeline.map((ev,i) => (
              <div key={i} style={{ display:'flex', gap:12, marginBottom:10, alignItems:'flex-start', position:'relative' }}>
                <div style={{ width:10, height:10, borderRadius:'50%', background:sevColor, flexShrink:0, marginTop:3, position:'absolute', left:'-18px', boxShadow:`0 0 6px ${sevColor}60` }} />
                <div style={{ paddingLeft:4 }}>
                  <div style={{ fontFamily:'var(--font-mono)', fontSize:10, color:sevColor, marginBottom:2 }}>{ev.date}</div>
                  <div style={{ fontSize:12, color:'var(--text-dim)' }}>{ev.event}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div style={{ display:'flex', gap:8, marginTop:14, flexWrap:'wrap' }}>
        <a href="/legal" className="btn btn-danger btn-sm" style={{ flex:1 }}>Generate Legal Doc</a>
        <a href="https://cybercivilrights.org/ccri-crisis-helpline/" target="_blank" rel="noopener noreferrer" className="btn btn-outline btn-sm" style={{ flex:1 }}>CCRI Crisis Line</a>
        <a href="https://www.ic3.gov" target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm" style={{ flex:1 }}>FBI IC3 Report</a>
      </div>
    </div>
  )
}

function LeakCard({ site, index }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const tc  = THREAT_COLOR[site.threat_level] || 'var(--amber)'
  const cls = (site.threat_level || '').toLowerCase()
  const contentUrl = site.content_url || site.url

  function copyUrl() {
    navigator.clipboard.writeText(contentUrl).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 1800)
    })
  }

  return (
    <div className={`leak-card ${cls}`} style={{ animationDelay:`${index*0.06}s`, animation:'fadeSlideUp .4s ease both' }}>
      <div className="leak-header" onClick={() => setOpen(o => !o)}>
        <div className="leak-icon" style={{ background:`${tc}12`, border:`1px solid ${tc}30`, color:tc }}>
          {site.icon || site.platform.slice(0,2).toUpperCase()}
        </div>
        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ display:'flex', gap:8, alignItems:'center', marginBottom:4, flexWrap:'wrap' }}>
            <span style={{ fontFamily:'var(--font-serif)', fontSize:15, fontWeight:700 }}>{site.platform}</span>
            <span className={`tag ${THREAT_TAG[site.threat_level]}`}>{site.threat_level}</span>
            {site.verified
              ? <span className="tag tag-cyan">VERIFIED MATCH</span>
              : <span className="tag tag-muted" style={{ fontSize:8 }}>RISK-BASED</span>}
          </div>
          {/* Real content URL — prominently shown */}
          <div style={{ display:'flex', alignItems:'center', gap:6, marginTop:2 }}>
            <span className="mono muted" style={{ fontSize:9, flexShrink:0, color:'var(--text-muted)' }}>CONTENT URL:</span>
            <span className="mono" style={{ fontSize:10, color:tc, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', flex:1 }}>{contentUrl}</span>
          </div>
        </div>
        <div style={{ display:'flex', gap:6, alignItems:'center', flexShrink:0 }}>
          <a href={contentUrl} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
             className="btn btn-ghost btn-sm" style={{ fontSize:10 }}>View ↗</a>
          <a href={site.report_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
             className="btn btn-danger btn-sm">Report</a>
          <a href={site.dmca_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
             className="btn btn-gold btn-sm">DMCA</a>
          <span style={{ color:'var(--text-muted)', fontSize:11, transition:'transform .2s', display:'inline-block', transform:open?'rotate(180deg)':'rotate(0deg)' }}>▼</span>
        </div>
      </div>

      {open && (
        <div className="leak-body">
          {/* Content URL box with copy button */}
          <div style={{ background:'var(--bg2)', border:`1px solid ${tc}30`, borderRadius:6, padding:'10px 14px', marginBottom:12 }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:6 }}>
              <span className="mono" style={{ color:tc, fontSize:9, letterSpacing:'.1em' }}>
                {site.verified ? '🔴 CONTENT FOUND AT THIS URL' : '⚠ RISK-ASSESSED PLATFORM URL'}
              </span>
              <button onClick={copyUrl} className="btn btn-ghost btn-sm" style={{ fontSize:9, padding:'3px 8px' }}>
                {copied ? '✓ COPIED' : 'COPY URL'}
              </button>
            </div>
            <div style={{ fontFamily:'var(--font-mono)', fontSize:11, color:'var(--text)', wordBreak:'break-all', lineHeight:1.6 }}>
              {contentUrl}
            </div>
            <div style={{ marginTop:8, display:'flex', gap:8, flexWrap:'wrap' }}>
              <a href={contentUrl} target="_blank" rel="noopener noreferrer"
                 className="btn btn-ghost btn-sm" style={{ fontSize:10 }}>
                ↗ Open Content Page
              </a>
              <a href={site.report_url} target="_blank" rel="noopener noreferrer"
                 className="btn btn-danger btn-sm" style={{ fontSize:10 }}>
                ⚑ Report This Content
              </a>
            </div>
          </div>

          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:8, marginBottom:12 }}>
            {[
              { label:'DETECTED',    val:site.date_detected,  color:'var(--text)' },
              { label:'EST. VIEWS',  val:site.views_estimate, color:tc },
              { label:'TAKEDOWN ETA',val:site.takedown_time,  color:'var(--text-dim)' },
            ].map(s => (
              <div key={s.label} style={{ background:'var(--surface)', border:'1px solid var(--line)', borderRadius:6, padding:'10px 12px' }}>
                <div className="mono muted" style={{ marginBottom:4, fontSize:9 }}>{s.label}</div>
                <div style={{ fontFamily:'var(--font-mono)', fontSize:12, fontWeight:600, color:s.color }}>{s.val}</div>
              </div>
            ))}
          </div>

          <div style={{ background:'var(--surface)', border:'1px solid var(--line)', borderRadius:6, padding:14, marginBottom:12 }}>
            <div className="mono" style={{ color:'var(--cyan)', marginBottom:8, fontSize:9 }}>REMOVAL PROTOCOL</div>
            <p style={{ fontSize:13, color:'var(--text-dim)', lineHeight:1.7 }}>{site.solution}</p>
            {site.law_ref && <div className="mono muted" style={{ marginTop:8, fontSize:9 }}>LEGAL BASIS: {site.law_ref}</div>}
          </div>

          <div style={{ marginBottom:12 }}>
            <div className="mono muted" style={{ marginBottom:8, fontSize:9 }}>DIRECT TAKEDOWN LINKS</div>
            <div className="action-grid">
              {(site.takedown_urls || []).map((link, i) => {
                const cls2 = ['action-link primary','action-link danger','action-link gold','action-link'][i % 4]
                return <a key={i} href={link.url} target="_blank" rel="noopener noreferrer" className={cls2}><span style={{ fontSize:10 }}>↗</span>{link.label}</a>
              })}
            </div>
          </div>

          {site.helplines && site.helplines.length > 0 && (
            <div style={{ background:'rgba(255,255,255,0.02)', border:'1px solid rgba(255,255,255,.08)', borderRadius:6, padding:'10px 14px', marginBottom:12 }}>
              <div className="mono" style={{ color:'var(--cyan)', marginBottom:8, fontSize:9 }}>VICTIM SUPPORT</div>
              <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
                {site.helplines.map((h, i) => <a key={i} href={h.url} target="_blank" rel="noopener noreferrer" className="btn btn-outline btn-sm">{h.label}</a>)}
              </div>
            </div>
          )}

          <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
            <a href={contentUrl} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm" style={{ flex:1 }}>↗ View Content Page</a>
            <a href={site.report_url} target="_blank" rel="noopener noreferrer" className="btn btn-danger btn-sm" style={{ flex:1 }}>{site.report_label || 'File Report'}</a>
            <a href={site.dmca_url} target="_blank" rel="noopener noreferrer" className="btn btn-gold btn-sm" style={{ flex:1 }}>{site.dmca_label || 'DMCA Notice'}</a>
            <a href="/legal" className="btn btn-outline btn-sm" style={{ flex:1 }}>Legal Doc</a>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Scan() {
  const [image, setImage]     = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [phase, setPhase]     = useState('')
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)
  const [drag, setDrag]       = useState(false)
  const fileRef = useRef()

  const PHASES = [
    'Initialising forensic models...','Running deepfake detection...',
    'Running NSFW explicit content detection...','Scanning Google for distributed copies...',
    'Scanning Bing visual search...','Building threat actor profile...','Generating LLM threat analysis...',
  ]

  function handleFile(f) {
    if (!f?.type.startsWith('image/')) return
    setImage(f); setPreview(URL.createObjectURL(f)); setResult(null); setError(null)
  }

  async function analyze() {
    setLoading(true); setError(null); setResult(null)
    let idx = 0
    const pt = setInterval(() => { idx = Math.min(idx+1, PHASES.length-1); setPhase(PHASES[idx]) }, 3200)
    setPhase(PHASES[0])
    try {
      const form = new FormData(); form.append('image', image)
      const res  = await fetch('/api/analyze', { method:'POST', body:form })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Analysis failed')
      setResult(data)
    } catch(e) { setError(e.message) }
    finally { clearInterval(pt); setLoading(false); setPhase('') }
  }

  // If the multi-model ensemble flagged AI Generated (CLIP >= 50%), upgrade the top
  // verdict card even when the weighted ensemble score is below the 0.65 threshold.
  // Deepfake always takes priority over AI Generated.
  const multiModelAiDetected = result &&
    (result.detection?.is_ai_generated ||
     Number(result.detection?.model_confidences?.ai_generated || 0) >= 50)

  const effectiveClassification = result
    ? (result.classification === 'Deepfake'   ? 'Deepfake'     // deepfake wins
       : multiModelAiDetected                 ? 'AI Generated' // CLIP override
       : result.classification)                                // internal verdict
    : null

  const vc = result
    ? (VERDICT[effectiveClassification] || VERDICT[result.verdict] || VERDICT.SUSPICIOUS)
    : null

  return (
    <main style={{ padding:'40px 0 72px' }}>
      <div className="wrap">
        <div className="a1" style={{ marginBottom:32 }}>
          <div className="label" style={{ marginBottom:10 }}>Image Forensic Scanner</div>
          <h2 style={{ marginBottom:8 }}>Deepfake · NSFW · Leak · Threat Intelligence</h2>
          <p style={{ fontSize:14, maxWidth:600 }}>
            Upload any image. Detects AI-generated fakes <em>and</em> explicit AI-generated content,
            finds every site where it has been distributed, identifies the likely threat actor behind the leak,
            and gives you direct takedown links for every platform.
          </p>
        </div>

        <div className="grid-2" style={{ gap:24, alignItems:'start' }}>
          <div className="a2">
            <div className="card" style={{ padding:0, overflow:'hidden', marginBottom:14 }}>
              <div style={{ padding:'11px 18px', borderBottom:'1px solid var(--line)', display:'flex', justifyContent:'space-between', alignItems:'center', background:'var(--bg2)' }}>
                <span className="mono" style={{ color:'var(--cyan)', fontSize:10 }}>EVIDENCE UPLOAD</span>
                <span className="mono muted">JPG · PNG · WEBP · 10 MB</span>
              </div>
              <div className={`upload-zone ${drag?'drag':''}`}
                style={{ border:'none', borderRadius:0, minHeight:280, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}
                onClick={() => fileRef.current.click()}
                onDragOver={e => { e.preventDefault(); setDrag(true) }}
                onDragLeave={() => setDrag(false)}
                onDrop={e => { e.preventDefault(); setDrag(false); handleFile(e.dataTransfer.files[0]) }}>
                {preview ? (
                  <div className="scan-wrap" style={{ width:'100%' }}>
                    <img src={preview} alt="target" style={{ width:'100%', maxHeight:280, objectFit:'cover', display:'block' }} />
                    {loading && <div className="scan-beam" />}
                  </div>
                ) : (
                  <>
                    <div style={{ width:60, height:60, borderRadius:12, marginBottom:18, background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,.1)', display:'flex', alignItems:'center', justifyContent:'center' }}>
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" stroke="var(--cyan)" strokeWidth="1.5" strokeLinecap="round"/>
                        <polyline points="17,8 12,3 7,8" stroke="var(--cyan)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        <line x1="12" y1="3" x2="12" y2="15" stroke="var(--cyan)" strokeWidth="1.5" strokeLinecap="round"/>
                      </svg>
                    </div>
                    <p className="mono" style={{ color:'var(--text-dim)', marginBottom:6 }}>Drop image or click to upload</p>
                    <p className="mono muted">JPG · PNG · WEBP · MAX 10MB</p>
                  </>
                )}
              </div>
            </div>
            <input ref={fileRef} type="file" accept="image/*" style={{ display:'none' }} onChange={e => handleFile(e.target.files[0])} />
            {image && <p className="mono muted" style={{ marginBottom:12, fontSize:10 }}>{image.name} · {(image.size/1024).toFixed(0)} KB</p>}
            <button className="btn btn-primary btn-md" onClick={analyze} disabled={loading||!image} style={{ width:'100%', fontSize:11 }}>
              {loading ? <><div className="spinner" style={{ width:15,height:15,borderWidth:2 }} />{phase||'Analysing...'}</> : 'Full Analysis — Deepfake · NSFW · Leaks · Threat Profile'}
            </button>
            {error && <div className="err" style={{ marginTop:12 }}>{error}</div>}

            {!result && !loading && (
              <div className="card" style={{ marginTop:18, padding:'16px 18px' }}>
                <div className="mono muted" style={{ marginBottom:14, fontSize:9 }}>ANALYSIS PIPELINE</div>
                {[
                  ['Deepfake detection via HuggingFace ViT (dima806 model)', 'var(--cyan)'],
                  ['NSFW / explicit nude AI content detection (Falconsai)', 'var(--red)'],
                  ['Google Lens + Bing reverse image search', 'var(--gold)'],
                  ['Platform classification + threat rating per URL', 'var(--amber)'],
                  ['Threat actor profiling from distribution patterns', 'var(--purple)'],
                  ['Direct report + DMCA links per platform', 'var(--green)'],
                ].map(([t,c]) => (
                  <div key={t} style={{ display:'flex', gap:10, alignItems:'flex-start', marginBottom:10 }}>
                    <div style={{ width:6, height:6, borderRadius:'50%', background:c, flexShrink:0, marginTop:5 }} />
                    <span style={{ fontSize:12, color:'var(--text-dim)' }}>{t}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="a3">
            {!result && !loading && (
              <div className="card" style={{ padding:'72px 24px', textAlign:'center' }}>
                <div style={{ fontFamily:'var(--font-serif)', fontSize:72, fontWeight:700, opacity:.04, marginBottom:14, color:'var(--cyan)', lineHeight:1 }}>DS</div>
                <p className="mono muted">SCANNER READY — AWAITING INPUT</p>
              </div>
            )}
            {loading && (
              <div className="card" style={{ padding:'48px 24px' }}>
                <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:20 }}>
                  <div className="spinner" style={{ width:44, height:44 }} />
                  <p className="mono" style={{ color:'var(--cyan)', textAlign:'center', fontSize:11 }}>{phase}</p>
                  <div style={{ width:'100%' }}>
                    {['Deepfake model inference (ViT)','NSFW explicit content detection','Google reverse image search','Bing visual search','Threat actor profiling','LLM analysis'].map(s => (
                      <div key={s} style={{ display:'flex', gap:10, alignItems:'center', marginBottom:10 }}>
                        <div className="spinner" style={{ width:12, height:12, borderWidth:1.5, opacity:.45 }} />
                        <span style={{ fontSize:12, color:'var(--text-muted)' }}>{s}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {result && vc && (
              <div className="a1">
                <div className={`card ${vc.cls}`} style={{ marginBottom:14, textAlign:'center', padding:'20px 22px' }}>
                  {/* Classification badge — primary 3-class label */}
                  <div style={{ marginBottom:8 }}>
                    <span className={`tag ${vc.tag}`} style={{ fontSize:11, padding:'5px 14px', letterSpacing:'.12em' }}>{vc.label}</span>
                  </div>
                  {/* Sub-classification detail */}
                  {effectiveClassification && (
                    <div className="mono" style={{ color:vc.color, fontSize:10, letterSpacing:'.08em', marginBottom:8, textTransform:'uppercase' }}>
                      {effectiveClassification === 'Deepfake'     ? '⚠ Face-Swap / Deepfake Detected' :
                       effectiveClassification === 'AI Generated' ? 'Full-Scene AI Synthesis Detected' :
                       '✓ Authentic Photograph'}
                    </div>
                  )}
                  <p style={{ fontSize:13, color:'var(--text-dim)', marginTop:4 }}>{vc.sub} · Confidence: {result.confidence}%</p>
                </div>

                <div className="card" style={{ marginBottom:14 }}>
                  <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginBottom:14 }}>
                    {[
                      { l:'RISK SCORE', v:`${result.risk_score}%`, c:vc.color },
                      { l:'FAKE PROB',  v:`${((result.raw_scores?.fake_probability||0)*100).toFixed(1)}%`, c:'var(--red)' },
                      { l:'NSFW SCORE', v:`${Math.round((result.nsfw?.nsfw_score||0)*100)}%`, c:result.nsfw?.is_explicit?'var(--red)':'var(--green)' },
                      { l:'LEAKS', v:result.total_leaks, c:result.total_leaks>0?'var(--amber)':'var(--green)' },
                    ].map(m => (
                      <div key={m.l} style={{ textAlign:'center', background:'var(--bg2)', borderRadius:6, padding:'10px 8px', border:'1px solid var(--line)' }}>
                        <div style={{ fontFamily:'var(--font-serif)', fontSize:22, fontWeight:700, color:m.c }}>{m.v}</div>
                        <div className="mono muted" style={{ marginTop:3, fontSize:8 }}>{m.l}</div>
                      </div>
                    ))}
                  </div>
                  <div className="progress">
                    <div className={`progress-bar ${result.risk_score>65?'red':result.risk_score>40?'amber':''}`} style={{ width:`${result.risk_score}%` }} />
                  </div>
                </div>

                <NSFWPanel nsfw={result.nsfw} />

                <div className="card" style={{ marginBottom:14 }}>
                  <div className="mono" style={{ color:'var(--text-muted)', marginBottom:12, fontSize:9 }}>FORENSIC INDICATORS</div>
                  {result.indicators?.map((ind,i) => (
                    <div key={i} style={{ display:'flex', gap:10, marginBottom:8, fontSize:13, color:'var(--text-dim)', lineHeight:1.55 }}>
                      <span style={{ color:vc.color, flexShrink:0 }}>›</span> {ind}
                    </div>
                  ))}
                </div>

                {/* Ensemble detection results */}
                {result.detection && (
                  <div className="card" style={{ marginBottom:14 }}>
                    <div className="mono" style={{ color:'var(--cyan)', marginBottom:12, fontSize:9 }}>MULTI-MODEL ENSEMBLE RESULTS</div>
                    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
                      {(() => {
                        // When AI Generated is DETECTED, Deepfake Face is also forced DETECTED.
                        // A fully AI-synthesised image always contains synthesised facial content.
                        const aiGenDetected =
                          result.detection.is_ai_generated ||
                          Number(result.detection.model_confidences?.ai_generated || 0) >= 50
                        return [
                          { l:'AI Generated',      bool:result.detection.is_ai_generated,                pct:result.detection.model_confidences?.ai_generated,     threshold:50 },
                          { l:'Deepfake Face',      bool:result.detection.is_deepfake || aiGenDetected,   pct:result.detection.model_confidences?.deepfake,          threshold:50 },
                          { l:'Forensic Artifacts', bool:result.detection.is_body_ai_generated,           pct:result.detection.model_confidences?.body_manipulation, threshold:40 },
                          { l:'Explicit Fake',      bool:result.detection.is_explicit_fake,               pct:result.detection.model_confidences?.explicit_fake,     threshold:50 },
                        ].map(m => {
                          // Show DETECTED if boolean is true OR if individual model confidence >= threshold
                          const detected = m.bool || (m.pct !== undefined && Number(m.pct) >= m.threshold)
                          return (
                          <div key={m.l} style={{ padding:'8px 12px', background:'var(--bg2)', borderRadius:6, border:`1px solid ${detected?'rgba(255,68,68,.25)':'var(--line)'}` }}>
                            <div className="mono muted" style={{ fontSize:9, marginBottom:4 }}>{m.l}</div>
                            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
                              <span className={`tag ${detected?'tag-red':'tag-green'}`}>{detected?'DETECTED':'CLEAN'}</span>
                              {m.pct !== undefined && <span className="mono muted" style={{ fontSize:10 }}>{Number(m.pct).toFixed(1)}%</span>}
                            </div>
                          </div>
                          )
                        })
                      })()}
                    </div>
                    {result.detection.explanation && (
                      <div style={{ marginTop:10, fontSize:12, color:'var(--text-dim)', fontStyle:'italic' }}>{result.detection.explanation}</div>
                    )}
                    {/* Raw model scores breakdown */}
                    {result.raw_scores && (
                      <div style={{ marginTop:12, padding:'10px 12px', background:'var(--bg2)', borderRadius:6, border:'1px solid var(--line)' }}>
                        <div className="mono muted" style={{ marginBottom:8, fontSize:9 }}>RAW MODEL SCORES</div>
                        <div style={{ display:'flex', gap:16, flexWrap:'wrap' }}>
                          {[
                            { l:'CLIP AI', v:result.raw_scores?.clip_ai_prob },
                            { l:'ViT FAKE', v:result.raw_scores?.deepfake_prob },
                            { l:'FORENSIC', v:result.raw_scores?.artifact_prob },
                            { l:'ENSEMBLE', v:result.raw_scores?.final_ensemble_score },
                          ].filter(m => m.v !== undefined).map(m => (
                            <div key={m.l} style={{ textAlign:'center' }}>
                              <div style={{ fontFamily:'var(--font-mono)', fontSize:14, fontWeight:700, color:'var(--cyan)' }}>{(m.v*100).toFixed(1)}%</div>
                              <div className="mono muted" style={{ fontSize:8 }}>{m.l}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Police Complaint — shown ONLY when internal classification is "Deepfake" */}
                <PoliceComplaintPanel complaint={result.police_complaint} result={result} />

                {result.llm_analysis && (
                  <div className="card card-cyan" style={{ marginBottom:14 }}>
                    <div className="mono" style={{ color:'var(--cyan)', marginBottom:10, fontSize:9 }}>AI ANALYSIS</div>
                    <p style={{ fontSize:14, fontFamily:'var(--font-serif)', lineHeight:1.75, marginBottom:14, color:'var(--text)' }}>{result.llm_analysis.summary}</p>
                    {result.llm_analysis.emotional_support && <blockquote>{result.llm_analysis.emotional_support}</blockquote>}
                  </div>
                )}

                {result.llm_analysis?.immediate_actions && (
                  <div className="card card-red" style={{ marginBottom:14 }}>
                    <div className="mono" style={{ color:'var(--red)', marginBottom:12, fontSize:9 }}>IMMEDIATE ACTIONS</div>
                    {result.llm_analysis.immediate_actions.map((a,i) => (
                      <div key={i} style={{ display:'flex', gap:12, marginBottom:10, alignItems:'flex-start' }}>
                        <span className="mono" style={{ color:'var(--red)', background:'rgba(255,68,68,.1)', padding:'2px 7px', borderRadius:3, flexShrink:0, fontSize:10 }}>{String(i+1).padStart(2,'0')}</span>
                        <span style={{ fontSize:13, color:'var(--text-dim)', lineHeight:1.55 }}>{a}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {result && result.threat_profile && (
          <div className="a1" style={{ marginTop:36 }}>
            <div className="divider">Threat Actor Intelligence</div>
            <ThreatProfilePanel profile={result.threat_profile} />
          </div>
        )}

        {result && (
          <div className="a1" style={{ marginTop:24 }}>
            <div className="divider">
              {result.total_leaks > 0
                ? `${result.total_leaks} Distribution Source${result.total_leaks>1?'s':''} Identified`
                : 'No Distributed Copies Found'}
            </div>
            {result.total_leaks > 0 ? (
              <>
                <div className="card card-red" style={{ marginBottom:20, padding:'16px 20px' }}>
                  <div style={{ display:'flex', gap:16, alignItems:'center', flexWrap:'wrap' }}>
                    <span className="dot dot-red" />
                    <div style={{ flex:1 }}>
                      <div style={{ fontFamily:'var(--font-serif)', fontSize:15, fontWeight:700, color:'var(--red)', marginBottom:4 }}>Content detected on {result.total_leaks} platform{result.total_leaks>1?'s':''}</div>
                      <p style={{ fontSize:13 }}>Expand each row to access platform-specific report links, DMCA portals, and victim support.</p>
                    </div>
                    <div style={{ display:'flex', gap:8, flexShrink:0 }}>
                      <a href="https://stopncii.org" target="_blank" rel="noopener noreferrer" className="btn btn-outline btn-sm">StopNCII →</a>
                      <a href="/legal" className="btn btn-danger btn-sm">Legal Toolkit →</a>
                    </div>
                  </div>
                </div>
                <div className="card" style={{ marginBottom:20, padding:'14px 18px', borderColor:'rgba(255,255,255,.08)' }}>
                  <div style={{ display:'flex', gap:12, alignItems:'center', flexWrap:'wrap' }}>
                    <div className="label" style={{ whiteSpace:'nowrap' }}>FASTEST ACTION:</div>
                    <p style={{ fontSize:13, flex:1 }}><strong style={{ color:'var(--text)' }}>StopNCII.org</strong> — cryptographic hash distributed to 50+ platforms simultaneously.</p>
                    <a href="https://stopncii.org" target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm" style={{ flexShrink:0 }}>Use StopNCII →</a>
                  </div>
                </div>
                {result.leaked_sites.map((site, i) => <LeakCard key={i} site={site} index={i} />)}
              </>
            ) : (
              <div className="card card-green" style={{ padding:'32px 28px', textAlign:'center' }}>
                <div style={{ fontFamily:'var(--font-serif)', fontSize:20, fontWeight:700, color:'var(--green)', marginBottom:10 }}>No Distribution Detected</div>
                <p style={{ fontSize:14, maxWidth:480, margin:'0 auto 20px' }}>No matching instances found. Activate continuous monitoring to stay protected.</p>
                <div style={{ display:'flex', gap:10, justifyContent:'center', flexWrap:'wrap' }}>
                  <a href="/dashboard" className="btn btn-outline btn-sm">Activate Monitoring</a>
                  <a href="https://stopncii.org" target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">StopNCII Pre-Protection</a>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
