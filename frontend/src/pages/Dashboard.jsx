import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const ALERTS = [
  { id:1, platform:'Telegram', time:'2h ago',  risk:'CRITICAL', status:'NEW',      msg:'High-confidence facial match detected — channel membership ~12,400. AI confidence: 89%.' },
  { id:2, platform:'Reddit',   time:'1d ago',  risk:'HIGH',     status:'REVIEWED', msg:'Possible match in r/deepfakes — 340 upvotes, 28 comments. Visual confidence: 71%.' },
  { id:3, platform:'X/Twitter', time:'2d ago', risk:'MEDIUM',   status:'REVIEWED', msg:'Borderline match in a thread with 1,200 impressions — flagged for manual review.' },
  { id:4, platform:'Bing Images','time':'3d ago', risk:'LOW',   status:'CLEARED',  msg:'Low-confidence match — cleared after manual review. Confirmed different individual.' },
]

const RISK_COLOR = { CRITICAL:'var(--red)', HIGH:'rgba(255,120,50,.9)', MEDIUM:'var(--amber)', LOW:'var(--green)' }
const RISK_TAG   = { CRITICAL:'tag-red', HIGH:'tag-red', MEDIUM:'tag-amber', LOW:'tag-green' }
const STATUS_C   = { NEW:'var(--red)', REVIEWED:'var(--amber)', CLEARED:'var(--green)' }
const STATUS_T   = { NEW:'tag-red', REVIEWED:'tag-amber', CLEARED:'tag-green' }

const PLATFORMS = [
  'Telegram','Reddit','X / Twitter','Facebook','Instagram','TikTok',
  'Discord','4chan','Bing Images','Google Images','OnlyFans','Pornhub',
  'MEGA','Dropbox','Imgur','YouTube','Pinterest','Tumblr','Snapchat','LinkedIn',
]

export default function Dashboard() {
  const [enrolled, setEnrolled] = useState(false)
  const nav = useNavigate()

  if (!enrolled) return (
    <main style={{ padding: '80px 0 100px' }}>
      <div className="wrap" style={{ maxWidth: 620 }}>
        <div className="a1" style={{ marginBottom: 32 }}>
          <div className="label" style={{ marginBottom: 12 }}>Monitoring Dashboard</div>
          <h2 style={{ marginBottom: 14 }}>Activate Continuous Protection</h2>
          <p style={{ lineHeight: 1.85, fontSize: 15 }}>
            Enroll your facial signature for 24/7 web monitoring. DeepShield scans continuously
            for any distribution of your image across 50M+ URLs, platforms, and private channels.
          </p>
        </div>

        <div className="card glow-card a2" style={{ marginBottom: 24 }}>
          <div className="mono muted" style={{ marginBottom: 18, fontSize: 9 }}>MONITORING PIPELINE</div>
          {[
            ['Upload 3 reference photos — system generates your unique perceptual hash signature.',   'var(--cyan)'],
            ['Continuous scanning across 50M+ URLs, social platforms, and Telegram channels.',        'var(--purple)'],
            ['Real-time notification when any facial match or threat is identified.',                 'var(--amber)'],
            ['One-click access to direct report links, DMCA portals, and legal document generation.','var(--red)'],
          ].map(([t, c], i) => (
            <div key={i} style={{ display: 'flex', gap: 14, marginBottom: i < 3 ? 16 : 0, alignItems: 'flex-start' }}>
              <span className="mono" style={{
                color: c, background: `${c}12`,
                padding: '3px 8px', borderRadius: 3, flexShrink: 0, fontSize: 10,
              }}>
                {String(i+1).padStart(2,'0')}
              </span>
              <span style={{ fontSize: 14, color: 'var(--text-dim)', lineHeight: 1.6 }}>{t}</span>
            </div>
          ))}
        </div>

        <div className="card a3" style={{ marginBottom: 24, padding: '14px 18px', borderColor: 'rgba(255,255,255,.08)' }}>
          <div className="label" style={{ marginBottom: 8 }}>PRIVACY GUARANTEE</div>
          <p style={{ fontSize: 13 }}>
            Your reference photos are hashed locally and never uploaded to any server.
            Monitoring uses perceptual hash comparison — your original images are never stored or transmitted.
          </p>
        </div>

        <button className="btn btn-primary btn-lg a4" style={{ width: '100%', fontSize: 12 }}
          onClick={() => setEnrolled(true)}>
          Activate Continuous Monitoring — Free
        </button>
      </div>
    </main>
  )

  return (
    <main style={{ padding: '40px 0 72px' }}>
      <div className="wrap">

        {/* Header */}
        <div className="a1" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32, flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div className="label" style={{ marginBottom: 10 }}>Monitoring Dashboard</div>
            <h2 style={{ marginBottom: 6 }}>Active Threat Monitor</h2>
            <p style={{ fontSize: 14 }}>Real-time surveillance across 50M+ URLs and 20 platform channels.</p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-danger btn-sm" onClick={() => setEnrolled(false)}>Pause Monitoring</button>
            <button className="btn btn-outline btn-sm" onClick={() => nav('/scan')}>Manual Scan</button>
            <button className="btn btn-primary btn-sm" onClick={() => nav('/legal')}>Legal Toolkit</button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid-4 a2" style={{ marginBottom: 28 }}>
          {[
            { val: '847K',  label: 'URLs Scanned',    color: 'var(--cyan)',   sub: 'Last 24 hours' },
            { val: '2',     label: 'Active Alerts',   color: 'var(--amber)',  sub: 'Requires review' },
            { val: '0',     label: 'Confirmed Leaks', color: 'var(--green)',  sub: 'This month' },
            { val: '99.2%', label: 'Uptime',          color: 'var(--purple)', sub: 'System status' },
          ].map((s, i) => (
            <div key={i} className="card" style={{ textAlign: 'center', borderTop: `2px solid ${s.color}35` }}>
              <div style={{
                fontFamily: 'var(--font-serif)', fontSize: 32, fontWeight: 700,
                color: s.color, textShadow: `0 0 25px ${s.color}35`,
              }}>{s.val}</div>
              <div className="mono" style={{ color: 'var(--text-dim)', marginTop: 5, fontSize: 10 }}>{s.label}</div>
              <div className="mono muted" style={{ marginTop: 3, fontSize: 9 }}>{s.sub}</div>
            </div>
          ))}
        </div>

        {/* Alert Feed */}
        <div className="card a3" style={{ padding: 0, overflow: 'hidden', marginBottom: 24 }}>
          <div style={{
            padding: '12px 18px', borderBottom: '1px solid var(--line)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            background: 'var(--bg2)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="dot dot-live" />
              <span className="mono" style={{ color: 'var(--cyan)', fontSize: 10 }}>ALERT FEED — LIVE</span>
            </div>
            <span className="tag tag-cyan">● MONITORING ACTIVE</span>
          </div>

          {ALERTS.map(alert => (
            <div key={alert.id} className="alert-row"
              style={{ borderLeft: `3px solid ${RISK_COLOR[alert.risk]}` }}>
              <div style={{
                width: 40, height: 40, background: `${RISK_COLOR[alert.risk]}12`,
                border: `1px solid ${RISK_COLOR[alert.risk]}30`,
                borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                <span className="mono" style={{ color: RISK_COLOR[alert.risk], fontSize: 11, fontWeight: 700 }}>
                  {alert.platform.slice(0,2).toUpperCase()}
                </span>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 5, flexWrap: 'wrap' }}>
                  <span style={{ fontFamily: 'var(--font-serif)', fontSize: 14, fontWeight: 700 }}>{alert.platform}</span>
                  <span className={`tag ${RISK_TAG[alert.risk]}`}>{alert.risk}</span>
                  <span className={`tag ${STATUS_T[alert.status]}`} style={{ color: STATUS_C[alert.status] }}>{alert.status}</span>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>{alert.msg}</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8, flexShrink: 0 }}>
                <span className="mono muted" style={{ fontSize: 9 }}>{alert.time}</span>
                {alert.status === 'NEW' && (
                  <button className="btn btn-danger btn-sm" onClick={() => nav('/legal')}>Take Action</button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Quick Response */}
        <div className="grid-3 a4" style={{ marginBottom: 24, gap: 14 }}>
          {[
            { title:'StopNCII Hash Protection', desc:'Hash your image and block re-uploads across 50+ platforms instantly.', color:'var(--cyan)', url:'https://stopncii.org', btn:'Activate Now' },
            { title:'CCRI Crisis Helpline', desc:'Immediate professional support from the Cyber Civil Rights Initiative.', color:'var(--red)', url:'https://cybercivilrights.org/ccri-crisis-helpline/', btn:'Get Help' },
            { title:'FBI IC3 Report', desc:'Report deepfake crimes to the FBI Internet Crime Complaint Center.', color:'var(--amber)', url:'https://www.ic3.gov', btn:'File Report' },
          ].map((r, i) => (
            <div key={i} className="card" style={{ borderTop: `2px solid ${r.color}35` }}>
              <div className="label" style={{ color: r.color, marginBottom: 10 }}>QUICK RESPONSE</div>
              <h4 style={{ fontFamily: 'var(--font-serif)', marginBottom: 8 }}>{r.title}</h4>
              <p style={{ fontSize: 13, marginBottom: 14 }}>{r.desc}</p>
              <a href={r.url} target="_blank" rel="noopener noreferrer" className="btn btn-outline btn-sm" style={{ width: '100%' }}>
                {r.btn} ↗
              </a>
            </div>
          ))}
        </div>

        {/* Platform Coverage */}
        <div className="card a5" style={{ padding: '16px 20px' }}>
          <div className="mono muted" style={{ marginBottom: 14, fontSize: 9 }}>PLATFORM COVERAGE — 20 ACTIVE CHANNELS</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {PLATFORMS.map(p => (
              <div key={p} style={{
                padding: '5px 12px', background: 'var(--bg2)',
                border: '1px solid var(--line)', borderRadius: 4,
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <span className="dot dot-live" style={{ width: 5, height: 5 }} />
                <span className="mono" style={{ fontSize: 10, color: 'var(--text-dim)' }}>{p}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </main>
  )
}
