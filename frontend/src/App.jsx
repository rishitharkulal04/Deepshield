import { useState, useEffect, useRef } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import LoaderScreen from './components/LoaderScreen.jsx'
import Landing   from './pages/Landing.jsx'
import Scan      from './pages/Scan.jsx'
import Assess    from './pages/Assess.jsx'
import Legal     from './pages/Legal.jsx'
import Dashboard from './pages/Dashboard.jsx'

/* ─── Shield Logo ─────────────────────────────────────────────────────────── */
function ShieldLogo({ size = 34 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 44" fill="none" xmlns="http://www.w3.org/2000/svg"
      style={{ filter: 'drop-shadow(0 0 8px rgba(207,207,207,0.2))' }}>
      {/* Outer hex shield */}
      <path d="M20 1L37 9.5V25C37 33.5 29.5 40.5 20 43C10.5 40.5 3 33.5 3 25V9.5L20 1Z"
        fill="rgba(207,207,207,0.04)" stroke="rgba(207,207,207,0.4)" strokeWidth="1.2"/>
      {/* Inner accent ring */}
      <path d="M20 5L33 12V25C33 31.5 27.5 37 20 39.5C12.5 37 7 31.5 7 25V12L20 5Z"
        fill="none" stroke="rgba(207,207,207,0.15)" strokeWidth=".6"/>
      {/* DS monogram */}
      <text x="20" y="27" textAnchor="middle"
        fontFamily="Georgia, Times New Roman, serif"
        fontSize="13" fontWeight="700"
        fill="#cfcfcf" letterSpacing="-0.5">DS</text>
      {/* Corner brackets */}
      <line x1="3" y1="9.5" x2="3" y2="14" stroke="rgba(207,207,207,0.5)" strokeWidth="1.5"/>
      <line x1="37" y1="9.5" x2="37" y2="14" stroke="rgba(207,207,207,0.5)" strokeWidth="1.5"/>
    </svg>
  )
}

/* ─── Sysbar ──────────────────────────────────────────────────────────────── */
function SysBar({ status }) {
  const [time, setTime] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="sysbar">
      <div className="sysbar-item">
        <span className={`dot ${status === 'online' ? 'dot-live' : 'dot-amber'}`} />
        <span>DEEPSHIELD</span>
        <span className="sysbar-val">v4.0</span>
      </div>
      <div className="sysbar-item">
        <span>ENGINE</span>
        <span className="sysbar-val">LOCAL · OFFLINE</span>
      </div>
      <div className="sysbar-item">
        <span>MODEL</span>
        <span className="sysbar-val">ViT FORENSIC DETECTOR</span>
      </div>
      <div className="sysbar-item">
        <span>LLM</span>
        <span className="sysbar-val">OLLAMA · STREAMING</span>
      </div>
      <div className="sysbar-item">
        <span>SCAN</span>
        <span className="sysbar-val">GOOGLE · BING</span>
      </div>
      <div className="sysbar-item sysbar-right">
        <span className="sysbar-val"
          style={{ fontVariantNumeric: 'tabular-nums' }}>
          {time.toLocaleTimeString('en-GB')}
        </span>
      </div>
    </div>
  )
}

/* ─── Alert Bar ───────────────────────────────────────────────────────────── */
function AlertBar({ status }) {
  if (status === 'checking')
    return <div className="alertbar alertbar-warn">CONNECTING TO LOCAL SERVER — ENSURE BACKEND IS RUNNING ON PORT 8000</div>
  if (status === 'offline')
    return <div className="alertbar alertbar-err">⚠ BACKEND OFFLINE — cd backend → python main.py — THEN REFRESH</div>
  return null
}

/* ─── Page Transition Wrapper ─────────────────────────────────────────────── */
function PageTransition({ children }) {
  const location  = useLocation()
  const key       = location.pathname
  const ref       = useRef()

  useEffect(() => {
    if (!ref.current) return
    ref.current.classList.remove('page-enter')
    void ref.current.offsetHeight            // force reflow
    ref.current.classList.add('page-enter')
  }, [key])

  return (
    <div ref={ref} className="page-enter">
      {children}
    </div>
  )
}

/* ─── App ─────────────────────────────────────────────────────────────────── */
export default function App() {
  const [status, setStatus] = useState('checking')
  const [loaderComplete, setLoaderComplete] = useState(false)

  useEffect(() => {
    fetch('/api/health')
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'))
  }, [])

  return (
    <>
      {!loaderComplete && <LoaderScreen onComplete={() => setLoaderComplete(true)} />}
      
      <AlertBar status={status} />

      {/* ── Navbar ── */}
      <nav className="nav">
        <NavLink to="/" className="nav-brand" style={{ fontFamily: 'Helvetica Neue, Helvetica, Arial, sans-serif', fontWeight: 300, letterSpacing: '0.15em', fontSize: 16 }}>
          <ShieldLogo size={28} style={{ marginRight: 8 }} /> DEEPSHIELD
        </NavLink>

        <div className="nav-links">
          <NavLink to="/"          end>Home</NavLink>
          <NavLink to="/scan">Scan</NavLink>
          <NavLink to="/assess">Assess</NavLink>
          <NavLink to="/legal">Legal</NavLink>
          <NavLink to="/dashboard">Dashboard</NavLink>
        </div>

        <div className="nav-status">
          <span className={`dot ${status === 'online' ? 'dot-live' : 'dot-amber'}`} />
          <span className="mono" style={{ fontSize: 9 }}>{status === 'online' ? 'SYSTEM ONLINE' : 'CONNECTING...'}</span>
        </div>
      </nav>

      {/* ── Routes with transition ── */}
      <PageTransition>
        <Routes>
          <Route path="/"          element={<Landing />} />
          <Route path="/scan"      element={<Scan />} />
          <Route path="/assess"    element={<Assess />} />
          <Route path="/legal"     element={<Legal />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </PageTransition>
    </>
  )
}
