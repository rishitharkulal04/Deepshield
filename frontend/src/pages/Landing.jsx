import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

/* ─── Node/Network Canvas Animation ─────────────────────────────────────── */
function NetworkCanvas() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animId
    let w, h

    function resize() {
      w = canvas.width = canvas.offsetWidth
      h = canvas.height = canvas.offsetHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const nodes = Array.from({ length: 14 }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.0004,
      vy: (Math.random() - 0.5) * 0.0004,
      r: Math.random() * 2.5 + 2,
      pulse: Math.random() * Math.PI * 2,
      center: false,
    }))

    // Mark center node as the hub
    nodes[0].r = 11
    nodes[0].x = 0.55
    nodes[0].y = 0.48
    nodes[0].vx = 0
    nodes[0].vy = 0
    nodes[0].center = true

    function draw() {
      ctx.clearRect(0, 0, w, h)

      const mapped = nodes.map(n => ({ ...n, px: n.x * w, py: n.y * h }))

      // Draw edges
      for (let i = 0; i < mapped.length; i++) {
        for (let j = i + 1; j < mapped.length; j++) {
          const dx = mapped[i].px - mapped[j].px
          const dy = mapped[i].py - mapped[j].py
          const dist = Math.sqrt(dx * dx + dy * dy)
          const maxDist = w * 0.35
          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.22
            ctx.beginPath()
            ctx.moveTo(mapped[i].px, mapped[i].py)
            ctx.lineTo(mapped[j].px, mapped[j].py)
            ctx.strokeStyle = `rgba(200,200,200,${alpha})`
            ctx.lineWidth = 0.6
            ctx.stroke()
          }
        }
      }

      // Draw nodes
      mapped.forEach((n, idx) => {
        nodes[idx].pulse += 0.02
        const glow = Math.sin(nodes[idx].pulse) * 0.25 + 0.75

        if (n.center) {
          // Big hub with ring
          const grad = ctx.createRadialGradient(n.px, n.py, 0, n.px, n.py, n.r)
          grad.addColorStop(0, `rgba(210,210,210,${glow})`)
          grad.addColorStop(1, `rgba(150,150,150,0.5)`)
          ctx.beginPath()
          ctx.arc(n.px, n.py, n.r, 0, Math.PI * 2)
          ctx.fillStyle = grad
          ctx.fill()

          // Outer ring
          ctx.beginPath()
          ctx.arc(n.px, n.py, n.r + 6, 0, Math.PI * 2)
          ctx.strokeStyle = `rgba(255,255,255,0.1)`
          ctx.lineWidth = 1
          ctx.stroke()

          // Inner dark dot
          ctx.beginPath()
          ctx.arc(n.px, n.py, 2.5, 0, Math.PI * 2)
          ctx.fillStyle = 'rgba(0,0,0,0.85)'
          ctx.fill()
        } else {
          ctx.beginPath()
          ctx.arc(n.px, n.py, n.r, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(150,150,150,${glow * 0.65})`
          ctx.fill()
        }

        // Move non-center nodes
        if (!n.center) {
          nodes[idx].x += nodes[idx].vx
          nodes[idx].y += nodes[idx].vy
          if (nodes[idx].x < 0 || nodes[idx].x > 1) nodes[idx].vx *= -1
          if (nodes[idx].y < 0 || nodes[idx].y > 1) nodes[idx].vy *= -1
          nodes[idx].x = Math.max(0, Math.min(1, nodes[idx].x))
          nodes[idx].y = Math.max(0, Math.min(1, nodes[idx].y))
        }
      })

      animId = requestAnimationFrame(draw)
    }
    draw()
    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
    />
  )
}

/* ─── Three.js Wireframe Icosahedron ─────────────────────────────────────── */
function WireframeObject() {
  const mountRef = useRef(null)

  useEffect(() => {
    let renderer, animId

    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'
    script.onload = () => {
      const THREE = window.THREE
      if (!mountRef.current) return

      const scene = new THREE.Scene()
      const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100)
      camera.position.z = 3.5

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
      renderer.setSize(420, 420)
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
      renderer.setClearColor(0x000000, 0)
      mountRef.current.appendChild(renderer.domElement)

      const geo = new THREE.IcosahedronGeometry(1.2, 1)
      const group = new THREE.Group()

      // Chromatic aberration — red
      const redMat = new THREE.MeshBasicMaterial({ color: 0xff1010, wireframe: true, opacity: 0.55, transparent: true })
      const redMesh = new THREE.Mesh(geo, redMat)
      redMesh.position.set(0.015, 0, 0)
      group.add(redMesh)

      // Blue
      const blueMat = new THREE.MeshBasicMaterial({ color: 0x1010ff, wireframe: true, opacity: 0.35, transparent: true })
      const blueMesh = new THREE.Mesh(geo, blueMat)
      blueMesh.position.set(-0.012, 0.012, 0)
      group.add(blueMesh)

      // Main white wireframe
      const mainMat = new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, opacity: 0.28, transparent: true })
      const mainMesh = new THREE.Mesh(geo, mainMat)
      group.add(mainMesh)

      // Circle ring
      const ringGeo = new THREE.RingGeometry(1.42, 1.45, 64)
      const ringMat = new THREE.MeshBasicMaterial({ color: 0xffffff, opacity: 0.1, transparent: true, side: THREE.DoubleSide })
      const ring = new THREE.Mesh(ringGeo, ringMat)
      ring.rotation.x = Math.PI / 2.5
      group.add(ring)

      scene.add(group)

      function animate() {
        animId = requestAnimationFrame(animate)
        group.rotation.y += 0.0028
        group.rotation.x += 0.0008
        renderer.render(scene, camera)
      }
      animate()
    }
    document.head.appendChild(script)

    return () => {
      cancelAnimationFrame(animId)
      if (renderer) {
        renderer.dispose()
        if (renderer.domElement.parentNode) {
          renderer.domElement.parentNode.removeChild(renderer.domElement)
        }
      }
    }
  }, [])

  return <div ref={mountRef} style={{ width: 420, height: 420 }} />
}

/* ─── Threat Visualization Visualization ─────────────────────────────────── */
function ThreatVisualization() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animId
    let w, h

    function resize() {
      w = canvas.width = canvas.offsetWidth
      h = canvas.height = canvas.offsetHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const threats = Array.from({ length: 8 }, (_, i) => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.0006,
      vy: (Math.random() - 0.5) * 0.0006,
      r: Math.random() * 4 + 3,
      pulse: Math.random() * Math.PI * 2,
      threatLevel: Math.random() * 100,
    }))

    // Central threat hub
    const hub = {
      x: 0.5,
      y: 0.5,
      r: 8,
      pulse: 0,
    }

    function draw() {
      ctx.clearRect(0, 0, w, h)

      const mapped = threats.map(t => ({ ...t, px: t.x * w, py: t.y * h }))
      const hubPixel = { x: hub.x * w, y: hub.y * h }

      // Draw threat connections
      mapped.forEach(t => {
        const dx = t.px - hubPixel.x
        const dy = t.py - hubPixel.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        const threatIntensity = t.threatLevel / 100
        const alpha = threatIntensity * 0.4

        // Connection lines with color gradient based on threat level
        const gradient = ctx.createLinearGradient(t.px, t.py, hubPixel.x, hubPixel.y)
        if (t.threatLevel > 70) {
          // Red for high threat
          gradient.addColorStop(0, `rgba(255, 50, 50, ${alpha})`)
          gradient.addColorStop(1, `rgba(255, 100, 100, 0)`)
        } else if (t.threatLevel > 40) {
          // Yellow for medium threat
          gradient.addColorStop(0, `rgba(255, 200, 50, ${alpha})`)
          gradient.addColorStop(1, `rgba(255, 150, 100, 0)`)
        } else {
          // Gray for low threat
          gradient.addColorStop(0, `rgba(150, 150, 150, ${alpha})`)
          gradient.addColorStop(1, `rgba(150, 150, 150, 0)`)
        }

        ctx.beginPath()
        ctx.moveTo(t.px, t.py)
        ctx.lineTo(hubPixel.x, hubPixel.y)
        ctx.strokeStyle = gradient.stroke || gradient
        ctx.lineWidth = threatIntensity * 2.5
        ctx.stroke()
      })

      // Draw threat nodes
      mapped.forEach((t, idx) => {
        threats[idx].pulse += 0.02
        const glow = Math.sin(threats[idx].pulse) * 0.3 + 0.7
        const threatIntensity = t.threatLevel / 100

        let color
        if (t.threatLevel > 70) {
          color = `rgba(255, 80, 80, ${glow * threatIntensity})`
        } else if (t.threatLevel > 40) {
          color = `rgba(255, 180, 50, ${glow * threatIntensity})`
        } else {
          color = `rgba(180, 180, 180, ${glow * threatIntensity})`
        }

        // Threat node
        ctx.beginPath()
        ctx.arc(t.px, t.py, t.r, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()

        // Threat aura
        ctx.beginPath()
        ctx.arc(t.px, t.py, t.r + 5, 0, Math.PI * 2)
        ctx.strokeStyle = color.replace(/[\d.]+\)$/g, (m) => Math.max(0, parseFloat(m) - 0.4).toString() + ')')
        ctx.lineWidth = 1
        ctx.stroke()

        // Move threat nodes
        threats[idx].x += threats[idx].vx
        threats[idx].y += threats[idx].vy
        if (threats[idx].x < 0 || threats[idx].x > 1) threats[idx].vx *= -1
        if (threats[idx].y < 0 || threats[idx].y > 1) threats[idx].vy *= -1
        threats[idx].x = Math.max(0, Math.min(1, threats[idx].x))
        threats[idx].y = Math.max(0, Math.min(1, threats[idx].y))
      })

      // Draw central hub
      hub.pulse += 0.025
      const hubGlow = Math.sin(hub.pulse) * 0.2 + 0.8

      ctx.beginPath()
      ctx.arc(hubPixel.x, hubPixel.y, hub.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(210, 210, 210, ${hubGlow})`
      ctx.fill()

      // Hub ring
      ctx.beginPath()
      ctx.arc(hubPixel.x, hubPixel.y, hub.r + 8, 0, Math.PI * 2)
      ctx.strokeStyle = `rgba(255, 255, 255, 0.15)`
      ctx.lineWidth = 2
      ctx.stroke()

      // Pulsing danger ring
      ctx.beginPath()
      ctx.arc(hubPixel.x, hubPixel.y, hub.r + 14, 0, Math.PI * 2)
      ctx.strokeStyle = `rgba(255, 100, 100, ${Math.sin(hub.pulse * 1.5) * 0.3 + 0.2})`
      ctx.lineWidth = 1.5
      ctx.stroke()

      animId = requestAnimationFrame(draw)
    }
    draw()
    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
    />
  )
}

/* ─── Scroll Reveal ──────────────────────────────────────────────────────── */
function Reveal({ children, delay = 0, style = {} }) {
  const ref = useRef()
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect() } },
      { threshold: 0.12 }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])
  return (
    <div ref={ref} style={{
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(36px)',
      transition: `opacity 0.75s ${delay}s cubic-bezier(0.16,1,0.3,1), transform 0.75s ${delay}s cubic-bezier(0.16,1,0.3,1)`,
      ...style,
    }}>
      {children}
    </div>
  )
}

/* ─── Main Landing ─────────────────────────────────────────────────────────── */
export default function Landing() {
  const nav = useNavigate()

  return (
    <main style={{ position: 'relative', overflow: 'hidden' }}>

      {/* ══ SECTION 1: HERO ══ */}
      <section className="deepshield-hero">
        <div className="deepshield-wrap" style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr',
          gap: 80, alignItems: 'center', minHeight: 520,
        }}>
          <div>
            <div className="deepshield-eyebrow a1">● ADVANCED THREAT DETECTION</div>
            <h1 className="deepshield-h1 a2">
              Detect Deepfakes.<br />
              <strong>Secure</strong><br />
              <span className="deepshield-h1-muted">Your Digital Identity.</span>
            </h1>
            <p className="deepshield-body-text a3" style={{ maxWidth: 480, marginBottom: 36 }}>
              AI-powered deepfake detection, NSFW content analysis, and real-time threat intelligence.
              Scan files, identify leaks across 50M+ URLs, and take immediate action 
              with one-click DMCA takedown tools. Security by default.
            </p>
            <div className="deepshield-tech-list a4">
              {[
                { label: 'ViT FORENSIC DETECTOR', active: true },
                { label: 'REAL-TIME LEAK SCANNING', active: true },
                { label: 'THREAT ACTOR PROFILING', active: true },
                { label: 'AUTOMATED DMCA TOOLKIT', active: true },
              ].map((t, i) => (
                <div key={i} className="deepshield-tech-item" style={{ opacity: t.active ? 1 : 0.35 }}>
                  {t.label}
                </div>
              ))}
            </div>
          </div>
          <div style={{ position: 'relative', height: 440 }}>
            <NetworkCanvas />
          </div>
        </div>
      </section>

      {/* ══ SECTION 2: FEATURES ══ */}
      <section className="deepshield-section">
        <div className="deepshield-wrap">
          <Reveal>
            <div style={{ textAlign: 'center', marginBottom: 72 }}>
              <div className="deepshield-eyebrow" style={{ justifyContent: 'center', marginBottom: 18 }}>
                ● INTELLIGENCE & PROTECTION
              </div>
              <h2 className="deepshield-h2-large">Comprehensive Threat Protection.</h2>
              <p className="deepshield-body-text" style={{ maxWidth: 680, margin: '20px auto 0', textAlign: 'center' }}>
                AI-powered forensic analysis, automated leak detection across the entire internet,
                intelligent threat profiling, and one-click legal document generation for 
                rapid response to deepfakes and image-based abuse.
              </p>
            </div>
          </Reveal>

          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr',
            border: '1px solid rgba(255,255,255,0.07)',
          }}>
            {[
              { label: 'DEEPFAKE DETECTION', title: 'AI-Powered', titleMuted: 'Image Analysis', body: 'Advanced ViT-based forensic model identifies AI-generated deepfakes, synthetic faces, and NSFW content with 95%+ accuracy. Zero false positives on authenticity verification.' },
              { label: 'LEAK DETECTION', title: 'Real-Time', titleMuted: 'Internet Scanning', body: 'Continuously scans 50M+ URLs, social platforms, Telegram channels, and private imageboards. Instant notification when your content is detected anywhere.' },
              { label: 'THREAT PROFILING', title: 'Threat Actor', titleMuted: 'Intelligence', body: 'Analyzes distribution patterns to identify likely threat actors, their modus operandi, origin signals, and confidence scoring. Tactical intelligence for law enforcement.' },
              { label: 'LEGAL AUTOMATION', title: 'DMCA & Legal', titleMuted: 'Toolkit', body: 'AI-generated legal documents, direct integration with Google, Meta, X, Reddit, TikTok, and law enforcement. Takedown in minutes, not days.' },
            ].map((card, i) => (
              <Reveal key={i} delay={i * 0.08}>
                <div className="deepshield-card" style={{
                  borderRight: i % 2 === 0 ? '1px solid rgba(255,255,255,0.07)' : 'none',
                  borderBottom: i < 2 ? '1px solid rgba(255,255,255,0.07)' : 'none',
                }}>
                  <div className="deepshield-card-label">{card.label}</div>
                  <h3 className="deepshield-card-title">
                    {card.title}<br />
                    <span style={{ color: 'rgba(255,255,255,0.28)' }}>{card.titleMuted}</span>
                  </h3>
                  <p className="deepshield-card-body">{card.body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ══ SECTION 3: STATEMENT ══ */}
      <section className="deepshield-section" style={{ background: '#111' }}>
        <div className="deepshield-wrap" style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr',
          gap: 80, alignItems: 'center',
        }}>
          <Reveal>
            <div>
              <div className="deepshield-eyebrow" style={{ marginBottom: 24 }}>● INCIDENT RESPONSE</div>
              <h2 className="deepshield-statement">
                Protect. Detect.<br />
                <strong>Respond.</strong><br />
                <span style={{ color: 'rgba(255,255,255,0.3)' }}>In seconds.</span>
              </h2>
              <p className="deepshield-body-text" style={{ marginTop: 28, marginBottom: 40, maxWidth: 460 }}>
                When deepfakes are detected, every second counts. DeepShield combines
                AI-powered forensics with automated legal response—from threat detection
                to law enforcement reporting, all integrated in one platform.
              </p>
              <button className="deepshield-btn" onClick={() => nav('/scan')}>
                START THREAT SCAN NOW
              </button>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <div style={{
                position: 'relative',
                background: 'rgba(255,255,255,0.025)',
                border: '1px solid rgba(255,255,255,0.07)',
                padding: 6,
                overflow: 'hidden',
              }}>
                <div style={{
                  position: 'absolute', top: 14, left: 14, zIndex: 2,
                  fontFamily: 'var(--font-mono)', fontSize: 9, letterSpacing: '0.1em',
                  color: 'rgba(255,255,255,0.38)', lineHeight: 1.7, pointerEvents: 'none',
                }}>
                  THREAT DISTRIBUTION<br />
                  REAL-TIME TRACKING
                </div>
                <div style={{
                  position: 'absolute', bottom: 14, right: 14, zIndex: 2,
                  fontFamily: 'var(--font-mono)', fontSize: 9, letterSpacing: '0.14em',
                  color: 'rgba(255,255,255,0.22)', pointerEvents: 'none',
                }}>
                  THREAT INTELLIGENCE ENGINE
                </div>
                <div style={{ width: 420, height: 420 }}>
                  <WireframeObject />
                </div>
              </div>
            </div>
          </Reveal>


        </div>
      </section>

      {/* ══ SECTION 4: BRAND ══ */}
      <section className="deepshield-brand-section">
        <div className="deepshield-wrap" style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
          <Reveal>
            <h1 className="deepshield-brand-name">DEEPSHIELD</h1>
            <p className="deepshield-brand-tagline">Securing the Digital World.</p>
            <div className="deepshield-glass-box">
              DeepShield is an advanced cybersecurity intelligence platform. We detect 
              deepfakes, find image leaks, profile threat actors, and automate legal response—
              all in real-time. Protection for modern threats.
            </div>
          </Reveal>
          <div style={{
            width: 1, height: 52, background: 'rgba(255,255,255,0.2)',
            margin: '40px auto 0',
          }} />
        </div>
      </section>

    </main>
  )
}