import { useState, useRef } from 'react'

/* ── Portal Data ──────────────────────────────────────────────────────────── */
const PORTALS = {
  dmca: [
    { name:'Google — DMCA Removal', auth:'GOOGLE LLC', url:'https://support.google.com/legal/troubleshooter/1114905', desc:'Remove URLs from Google Search results, Images, and Discover.', type:'SEARCH', color:'var(--cyan)' },
    { name:'Bing / Microsoft DMCA', auth:'MICROSOFT CORP', url:'https://www.microsoft.com/en-us/concern/dmca', desc:'Remove infringing content from Bing Search, Images, and Microsoft services.', type:'SEARCH', color:'var(--cyan)' },
    { name:'Lumen Database — Public Record', auth:'LUMEN / BERKMAN KLEIN', url:'https://lumendatabase.org/notices/new', desc:'File your DMCA notice in the publicly-indexed Lumen Database for permanent legal record.', type:'LEGAL RECORD', color:'var(--purple)' },
    { name:'Reddit — Copyright Report', auth:'REDDIT INC', url:'https://www.redditinc.com/policies/dmca', desc:'Submit DMCA takedown to Reddit Trust & Safety for post and media removal.', type:'PLATFORM', color:'var(--amber)' },
    { name:'X / Twitter — DMCA Notice', auth:'X CORP', url:'https://help.twitter.com/forms/dmca', desc:'Submit DMCA notice to X/Twitter for removal from timelines and search.', type:'PLATFORM', color:'var(--amber)' },
    { name:'Meta — DMCA / NCII Report', auth:'META PLATFORMS', url:'https://www.facebook.com/help/contact/634636770043106', desc:'Submit to Meta for simultaneous removal across Facebook and Instagram.', type:'PLATFORM', color:'var(--amber)' },
    { name:'Cloudflare Abuse Report', auth:'CLOUDFLARE INC', url:'https://abuse.cloudflare.com/', desc:"If the host uses Cloudflare, file directly to reach the hosting provider's abuse team.", type:'HOSTING', color:'var(--text-muted)' },
    { name:'TikTok — Copyright Report', auth:'BYTEDANCE LTD', url:'https://www.tiktok.com/legal/copyright-policy', desc:'File DMCA takedown request to TikTok for video and image content removal.', type:'PLATFORM', color:'var(--amber)' },
  ],
  police: [
    { name:'FBI Internet Crime Complaint Center', auth:'FEDERAL BUREAU OF INVESTIGATION', url:'https://www.ic3.gov', desc:'Official US federal reporting portal for online crimes including deepfake exploitation and sextortion.', type:'FEDERAL LAW', color:'var(--red)' },
    { name:'CCRI Crisis Helpline', auth:'CYBER CIVIL RIGHTS INITIATIVE', url:'https://cybercivilrights.org/ccri-crisis-helpline/', desc:'Immediate crisis support. CCRI guides victims through law enforcement reporting and legal options.', type:'VICTIM SUPPORT', color:'var(--cyan)' },
    { name:'StopNCII — Hash Protection', auth:'INTERNET WATCH FOUNDATION', url:'https://stopncii.org', desc:'Creates a hash of your image and distributes it to 50+ platforms, preventing re-upload globally.', type:'MULTI-PLATFORM', color:'var(--green)' },
    { name:'UK — Report Harmful Content', auth:'REPORTHARMFULCONTENT.COM', url:'https://reportharmfulcontent.com/', desc:'UK-based reporting service for NCII, deepfakes, and intimate image abuse with direct platform links.', type:'UK LAW', color:'var(--cyan)' },
    { name:'UK — Action Fraud', auth:'CITY OF LONDON POLICE', url:'https://www.actionfraud.police.uk/', desc:'UK national reporting centre for fraud and cybercrime including deepfake sextortion.', type:'UK LAW', color:'var(--cyan)' },
    { name:'Australia — eSafety Commissioner', auth:'ESAFETY COMMISSIONER AU', url:'https://www.esafety.gov.au/report/image-based-abuse', desc:'Australian government portal for reporting image-based abuse including AI-generated deepfakes.', type:'AU LAW', color:'var(--cyan)' },
    { name:'India — Cyber Crime Portal', auth:'MINISTRY OF HOME AFFAIRS, INDIA', url:'https://cybercrime.gov.in', desc:'Indian national cyber crime reporting portal. File complaint under IT Act 2000 and DEFIANCE equivalents.', type:'INDIA LAW', color:'var(--cyan)' },
    { name:'National Centre for Missing & Exploited Children', auth:'NCMEC', url:'https://www.cybertipline.org', desc:'Report AI-generated CSAM or exploitation material to the US national cyber tipline.', type:'CHILD SAFETY', color:'var(--red)' },
  ],
  platform: [
    { name:'StopNCII — Multi-Platform Hash Block', auth:'INTERNET WATCH FOUNDATION', url:'https://stopncii.org', desc:'Fastest protection available — creates a cryptographic hash distributed to 50+ partner platforms simultaneously.', type:'MULTI-PLATFORM', color:'var(--green)' },
    { name:'Telegram — Report Abuse', auth:'TELEGRAM FZ LLC', url:'https://telegram.org/support', desc:'Report NCII content on Telegram. Use @SpamBot in-app or email abuse@telegram.org.', type:'PLATFORM', color:'var(--cyan)' },
    { name:'X / Twitter — NCII Report', auth:'X CORP', url:'https://help.twitter.com/forms/private_information', desc:'Report non-consensual intimate imagery (including deepfakes) to X Trust & Safety.', type:'PLATFORM', color:'var(--cyan)' },
    { name:'Reddit — Non-Consensual Images', auth:'REDDIT INC', url:'https://www.reddit.com/report', desc:"Report NCII to Reddit. Fast removal under Reddit's strict NCII policy — typically within 24 hours.", type:'PLATFORM', color:'var(--cyan)' },
    { name:'Meta — Facebook & Instagram', auth:'META PLATFORMS', url:'https://www.facebook.com/help/contact/567360covered', desc:'Report NCII to Meta for simultaneous removal across Facebook and Instagram.', type:'PLATFORM', color:'var(--cyan)' },
    { name:'TikTok — Report NCII', auth:'BYTEDANCE LTD', url:'https://www.tiktok.com/legal/report/privacy', desc:'Submit NCII removal request to TikTok via in-app report or the privacy request portal.', type:'PLATFORM', color:'var(--cyan)' },
    { name:'Discord — Safety Centre', auth:'DISCORD INC', url:'https://discord.com/safety', desc:'Report server or user distributing NCII. Discord terminates accounts and cooperates with law enforcement.', type:'PLATFORM', color:'var(--cyan)' },
    { name:'Google — Remove Sensitive Content', auth:'GOOGLE LLC', url:'https://support.google.com/legal/answer/1120734', desc:'Remove NCII from Google Search using the dedicated sensitive content removal tool.', type:'SEARCH', color:'var(--cyan)' },
  ],
}

const DOC_TYPES = [
  { value:'dmca',     label:'DMCA Takedown',    color:'var(--cyan)',   desc:'Copyright removal — Section 512(c)' },
  { value:'police',   label:'Police Report',    color:'var(--red)',    desc:'Statement for law enforcement' },
  { value:'platform', label:'Platform Removal', color:'var(--amber)',  desc:'Trust & Safety removal request' },
]

function PortalRow({ portal }) {
  const initials = portal.name.split(' ').slice(0,2).map(w => w[0]).join('')
  return (
    <div className="portal-row">
      <div className="portal-icon" style={{ color:portal.color, borderColor:`${portal.color}30`, background:`${portal.color}0a` }}>
        {initials}
      </div>
      <div className="portal-body">
        <div className="portal-name">{portal.name}</div>
        <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:4, marginTop:3 }}>
          <span className="mono muted" style={{ fontSize:8 }}>{portal.auth}</span>
          <span className="tag tag-muted" style={{ fontSize:8, color:portal.color }}>{portal.type}</span>
        </div>
        <div className="portal-desc">{portal.desc}</div>
      </div>
      <div className="portal-actions">
        <a href={portal.url} target="_blank" rel="noopener noreferrer" className="btn btn-outline btn-sm">
          Submit Report ↗
        </a>
      </div>
    </div>
  )
}

/* ── Main Legal Page ──────────────────────────────────────────────────────── */
export default function Legal() {
  const [form, setForm] = useState({ name:'', platform:'', url:'', incident_date:'', doc_type:'dmca' })
  const [loading, setLoading]   = useState(false)
  const [doc, setDoc]           = useState(null)
  const [streaming, setStreaming] = useState(false)
  const [error, setError]       = useState(null)
  const [copied, setCopied]     = useState(false)
  const [activeTab, setActiveTab] = useState('generate')
  const docRef = useRef('')

  const set = (k, v) => setForm(f => ({...f, [k]:v}))

  async function generate() {
    setLoading(true); setStreaming(true); setError(null); setDoc(null); docRef.current = ''
    try {
      const res = await fetch('/api/legal/stream', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form)
      })
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed') }
      const reader  = res.body.getReader()
      const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        docRef.current += decoder.decode(value, { stream:true })
        setDoc(docRef.current)
      }
      setStreaming(false)
    } catch(e) {
      setError(e.message)
      setStreaming(false)
    } finally {
      setLoading(false)
    }
  }

  function copy() {
    if (!doc) return
    navigator.clipboard.writeText(doc)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function openGmail() {
    if (!doc) return
    const subject = form.doc_type === 'police'
      ? 'URGENT: Deepfake Content Complaint – Request for Investigation'
      : form.doc_type === 'dmca'
      ? 'DMCA Takedown Notice – Deepfake Content Removal Request'
      : 'Platform Content Removal Request – Deepfake Media'
    const to = form.doc_type === 'police' ? 'cybercrime%40india.gov.in' : ''
    const url =
      `https://mail.google.com/mail/?view=cm&fs=1` +
      (to ? `&to=${to}` : '') +
      `&su=${encodeURIComponent(subject)}` +
      `&body=${encodeURIComponent(doc)}`
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  const dt = DOC_TYPES.find(d => d.value === form.doc_type)

  return (
    <main style={{ padding:'40px 0 72px' }}>
      <div className="wrap">

        <div className="a1" style={{ marginBottom:32 }}>
          <div className="label" style={{ marginBottom:10 }}>Legal Operations</div>
          <h2 style={{ marginBottom:8 }}>Legal Toolkit & Reporting Portals</h2>
          <p style={{ fontSize:14, maxWidth:580 }}>
            Generate legally-formatted documents with your local LLM, or navigate directly
            to DMCA portals, law enforcement reporting, and platform Trust & Safety teams.
          </p>
        </div>

        {/* Tabs */}
        <div className="tabs a2">
          {[
            { id:'generate', label:'Generate Document' },
            { id:'dmca',     label:'DMCA Portals' },
            { id:'police',   label:'Law Enforcement' },
            { id:'platform', label:'Platform Reports' },
          ].map(t => (
            <button key={t.id} className={`tab ${activeTab === t.id ? 'active' : ''}`}
              onClick={() => setActiveTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Generate Document Tab */}
        {activeTab === 'generate' && (
          <div className="grid-2 a1" style={{ gap:24, alignItems:'start' }}>
            <div>
              <div className="card" style={{ marginBottom:14 }}>
                <div className="mono muted" style={{ marginBottom:14, fontSize:9 }}>DOCUMENT TYPE</div>
                <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
                  {DOC_TYPES.map(d => (
                    <div key={d.value} onClick={() => set('doc_type', d.value)}
                      style={{
                        padding:'12px 16px', borderRadius:6, cursor:'pointer',
                        border:`1px solid ${form.doc_type === d.value ? d.color : 'var(--line)'}`,
                        background: form.doc_type === d.value ? `${d.color}08` : 'var(--bg2)',
                        transition:'all .2s',
                      }}>
                      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                        <span style={{ fontFamily:'var(--font-serif)', fontWeight:600, color: form.doc_type === d.value ? d.color : 'var(--text)' }}>{d.label}</span>
                        {form.doc_type === d.value && <span className="tag" style={{ color:d.color, borderColor:`${d.color}40` }}>SELECTED</span>}
                      </div>
                      <div className="mono muted" style={{ marginTop:4, fontSize:9 }}>{d.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <div className="input-label">Your Full Name</div>
                <input className="input" style={{ marginBottom:14 }}
                  placeholder="Full legal name..."
                  value={form.name} onChange={e => set('name', e.target.value)} />

                <div className="input-label">Platform / Website</div>
                <input className="input" style={{ marginBottom:14 }}
                  placeholder="e.g. Telegram, Reddit, Twitter..."
                  value={form.platform} onChange={e => set('platform', e.target.value)} />

                <div className="input-label">Content URL (if known)</div>
                <input className="input" style={{ marginBottom:14 }}
                  placeholder="https://..."
                  value={form.url} onChange={e => set('url', e.target.value)} />

                <div className="input-label">Incident Date</div>
                <input className="input" type="date" style={{ marginBottom:14 }}
                  value={form.incident_date} onChange={e => set('incident_date', e.target.value)} />

                <button className="btn btn-primary btn-md" onClick={generate}
                  disabled={loading || !form.name.trim() || !form.platform.trim()}
                  style={{ width:'100%' }}>
                  {loading ? <><div className="spinner" style={{ width:15,height:15,borderWidth:2 }} />Generating...</> : `Generate ${dt?.label || 'Document'}`}
                </button>
                {error && <div className="err" style={{ marginTop:12 }}>{error}</div>}
              </div>
            </div>

            <div>
              {!doc && !loading && (
                <div className="card" style={{ padding:'64px 24px', textAlign:'center' }}>
                  <div style={{ fontFamily:'var(--font-serif)', fontSize:56, fontWeight:700, opacity:.04, color:'var(--cyan)', marginBottom:14 }}>§</div>
                  <p className="mono muted">COMPLETE THE FORM TO GENERATE A LEGAL DOCUMENT</p>
                </div>
              )}
              {(doc || streaming) && (
                <div className="card" style={{ padding:0, overflow:'hidden' }}>
                  {/* Header bar */}
                  <div style={{
                    padding:'11px 18px', borderBottom:'1px solid var(--line)',
                    display:'flex', justifyContent:'space-between', alignItems:'center',
                    background:'var(--bg2)', flexWrap:'wrap', gap:8,
                  }}>
                    <div style={{ display:'flex', gap:10, alignItems:'center' }}>
                      {streaming && <div className="dot dot-live" />}
                      <span className="mono" style={{ color: dt?.color || 'var(--cyan)', fontSize:10 }}>
                        {dt?.label.toUpperCase() || 'DOCUMENT'} {streaming ? '— STREAMING' : '— COMPLETE'}
                      </span>
                      {!streaming && doc && (
                        <span className="mono muted" style={{ fontSize:9 }}>— editable below</span>
                      )}
                    </div>
                    {/* Action buttons — shown only when generation is complete */}
                    {!streaming && doc && (
                      <div style={{ display:'flex', gap:8 }}>
                        <button className="btn btn-ghost btn-sm" onClick={copy}>
                          {copied ? '✓ COPIED' : 'Copy Text'}
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={openGmail}
                          title={form.doc_type === 'police'
                            ? 'Open Gmail pre-filled to cybercrime@india.gov.in'
                            : 'Open Gmail pre-filled with this document'}
                        >
                          📧 Send Mail
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Editable document area */}
                  <textarea
                    value={doc || ''}
                    onChange={e => setDoc(e.target.value)}
                    readOnly={streaming}
                    placeholder={streaming ? '' : 'Edit the document here before sending...'}
                    style={{
                      width: '100%',
                      minHeight: 420,
                      maxHeight: 620,
                      resize: 'vertical',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                      color: 'var(--text-dim)',
                      background: 'var(--bg)',
                      border: 'none',
                      outline: 'none',
                      padding: '20px 22px',
                      lineHeight: 1.75,
                      boxSizing: 'border-box',
                      display: 'block',
                    }}
                  />

                </div>
              )}
            </div>
          </div>
        )}

        {/* Portal Tabs */}
        {['dmca','police','platform'].includes(activeTab) && (
          <div className="a1">
            <div className="card" style={{ padding:'0 20px' }}>
              {PORTALS[activeTab].map((p, i) => <PortalRow key={i} portal={p} />)}
            </div>
          </div>
        )}

      </div>
    </main>
  )
}
