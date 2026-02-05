import { useEffect, useState } from 'react'
import './App.css'

const IconSkull = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <circle cx="12" cy="10" r="6.5" fill="currentColor" />
    <circle cx="9.5" cy="10" r="1.4" fill="#0b0d12" />
    <circle cx="14.5" cy="10" r="1.4" fill="#0b0d12" />
    <rect x="9" y="14.6" width="6" height="3.4" rx="1.2" fill="currentColor" />
  </svg>
)

const IconBolt = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path
      d="M13 2 4 14h6l-1 8 9-12h-6z"
      fill="currentColor"
    />
  </svg>
)

const IconClock = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="2" />
    <path
      d="M12 8v4l3 2"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
)

const IconGauge = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path
      d="M4 15a8 8 0 0 1 16 0"
      stroke="currentColor"
      strokeWidth="2"
      fill="none"
      strokeLinecap="round"
    />
    <circle cx="12" cy="15" r="2" fill="currentColor" />
    <path
      d="M12 12.5 16 9"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
)

function App() {
  const initialMode = import.meta.env.VITE_BACKEND || 'SIM'
  const disableGrpc = ['1', 'true', 'yes'].includes(
    String(import.meta.env.VITE_DISABLE_GRPC || '').toLowerCase(),
  )
  const normalizedMode = initialMode === 'Light-weight Demo' ? 'SIM' : initialMode
  const [mode, setMode] = useState(disableGrpc ? 'SIM' : normalizedMode)
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState('')
  const [workers, setWorkers] = useState([])
  const [why, setWhy] = useState([])
  const [selectedWorker, setSelectedWorker] = useState('A')
  const [scale, setScale] = useState(3)
  const [scaleStatus, setScaleStatus] = useState('local')
  const [scaleError, setScaleError] = useState('')
  const [routingMode, setRoutingMode] = useState('least_queue')
  const [killWorker, setKillWorker] = useState(false)
  const [delayYellow, setDelayYellow] = useState(false)
  const [delayRed, setDelayRed] = useState(false)
  const [rateLimit, setRateLimit] = useState(false)
  const [chatHistory, setChatHistory] = useState([])
  const [error, setError] = useState('')
  const selectedWorkerData =
    workers.find((worker) => worker.label === selectedWorker) || workers[0]

  useEffect(() => {
    const hydrateState = (data) => {
      if (!data) return
      if (data.scale) setScale(data.scale)
      if (data.routing_mode) setRoutingMode(data.routing_mode)
      if (typeof data.kill_worker === 'boolean') setKillWorker(data.kill_worker)
      if (typeof data.delay_s === 'number') {
        setDelayYellow(data.delay_s >= 2)
      }
      if (typeof data.error_rate === 'number') {
        setDelayRed(data.error_rate > 0)
      }
      if (typeof data.rate_limit === 'number') {
        setRateLimit(data.rate_limit <= 5)
      }
      if (data.backend) {
        const nextMode = data.backend === 'GRPC' ? 'GRPC' : 'SIM'
        setMode(disableGrpc ? 'SIM' : nextMode)
      }
      if (data.selected_worker) setSelectedWorker(data.selected_worker)
      if (Array.isArray(data.why)) setWhy(data.why)
      if (Array.isArray(data.workers_detail)) setWorkers(data.workers_detail)
      if (data.scale_status) setScaleStatus(data.scale_status)
      if (typeof data.scale_error === 'string') setScaleError(data.scale_error)
    }

    const loadState = async () => {
      try {
        const res = await fetch('/api/state')
        if (!res.ok) return
        const data = await res.json()
        hydrateState(data)
      } catch {
        // ignore
      }
    }
    loadState()
  }, [])

  const updateState = async (patch) => {
    const payload = { backend: mode, ...patch }
    try {
      const res = await fetch('/api/state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) return
      const data = await res.json()
      if (data.scale) setScale(data.scale)
      if (data.routing_mode) setRoutingMode(data.routing_mode)
      if (typeof data.kill_worker === 'boolean') setKillWorker(data.kill_worker)
      if (typeof data.delay_s === 'number') {
        setDelayYellow(data.delay_s >= 2)
      }
      if (typeof data.error_rate === 'number') {
        setDelayRed(data.error_rate > 0)
      }
      if (typeof data.rate_limit === 'number') {
        setRateLimit(data.rate_limit <= 5)
      }
      if (data.backend) {
        const nextMode = data.backend === 'GRPC' ? 'GRPC' : 'SIM'
        setMode(disableGrpc ? 'SIM' : nextMode)
      }
      if (data.selected_worker) setSelectedWorker(data.selected_worker)
      if (Array.isArray(data.why)) setWhy(data.why)
      if (Array.isArray(data.workers_detail)) setWorkers(data.workers_detail)
      if (data.scale_status) setScaleStatus(data.scale_status)
      if (typeof data.scale_error === 'string') setScaleError(data.scale_error)
    } catch {
      setError('Could not reach the API server.')
    }
  }

  const handleSend = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const delay = delayRed || delayYellow ? 2 : 0
      const errorRate = delayRed ? 0.2 : 0
      const rateLimitValue = rateLimit ? 5 : 60

      const res = await fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          backend: mode,
          scale,
          routing_mode: routingMode,
          kill_worker: killWorker,
          delay_s: delay,
          error_rate: errorRate,
          rate_limit: rateLimitValue,
        }),
      })
      const data = await res.json()
      if (!res.ok || data.error) {
        setError(data.error || 'Request failed.')
      }
      setResponse(data.text || '')
      setWhy(data.why || [])
      setWorkers(data.workers_detail || [])
      setSelectedWorker(data.selected_worker || 'A')
      if (data.scale_status) setScaleStatus(data.scale_status)
      if (typeof data.scale_error === 'string') setScaleError(data.scale_error)
      if (data.mode) {
        const nextMode = data.mode === 'GRPC' ? 'GRPC' : 'SIM'
        setMode(disableGrpc ? 'SIM' : nextMode)
      }
      setChatHistory((prev) => [
        ...prev,
        { role: 'user', text: prompt },
        { role: 'assistant', text: data.text || '' },
      ])
      setPrompt('')
    } catch {
      setError('Could not reach the API server.')
    } finally {
      setLoading(false)
    }
  }

  const handleModeChange = (nextMode) => {
    if (disableGrpc && nextMode === 'GRPC') return
    setMode(nextMode)
    updateState({ backend: nextMode })
  }

  const handleScaleChange = (value) => {
    setScale(value)
    updateState({ scale: value })
  }

  const handleRoutingChange = (value) => {
    setRoutingMode(value)
    updateState({ routing_mode: value })
  }

  const handleDelay = (nextYellow, nextRed) => {
    setDelayYellow(nextYellow)
    setDelayRed(nextRed)
    const delay = nextYellow || nextRed ? 2 : 0
    const errorRate = nextRed ? 0.2 : 0
    updateState({ delay_s: delay, error_rate: errorRate })
  }

  const modeLabel = mode === 'SIM' ? 'Light-weight Demo' : 'GRPC'

  return (
    <div className="shell">
      <header className="topbar">
        <div className="window-controls">
          <span className="dot red" />
          <span className="dot yellow" />
          <span className="dot green" />
        </div>
        <div className="title-block">
          <div className="title-icon" />
          <div>
            <h1>LLM Inference Control Tower</h1>
            <p className="subtitle">Mode: {modeLabel}</p>
          </div>
        </div>
        <div className="mode-switch">
          <span>Mode</span>
          <div className="mode-toggle">
            <button
              type="button"
              className={mode === 'SIM' ? 'active' : ''}
              title="Run the local simulated worker pool"
              onClick={() => handleModeChange('SIM')}
            >
              Light-weight Demo
            </button>
            <button
              type="button"
              className={`${
                mode === 'GRPC' ? 'active' : ''
              }${disableGrpc ? ' disabled' : ''}`}
              title={
                disableGrpc
                  ? 'gRPC requires a local install. Download and run locally.'
                  : 'Send requests to the gRPC backend'
              }
              onClick={() => handleModeChange('GRPC')}
            >
              gRPC
            </button>
          </div>
        </div>
        <div className="scale">
          <span>Scale: {scale}</span>
          <input
            type="range"
            min="1"
            max="5"
            value={scale}
            onChange={(e) => handleScaleChange(Number(e.target.value))}
            style={{ '--percent': `${((scale - 1) / 4) * 100}%` }}
            title="Number of workers (SIM) or replicas (gRPC)"
          />
          <div className="ticks">
            {[1, 2, 3, 4, 5].map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
          <div className={`scale-status ${scaleStatus}`}>
            {scaleStatus === 'error'
              ? `Scale failed${scaleError ? `: ${scaleError}` : ''}`
              : scaleStatus === 'ok'
              ? 'Scaled in Kubernetes'
              : 'Local scale'}
          </div>
        </div>
      </header>

      <div className="main-grid">
        <aside className="panel chat-panel">
          <h2>Chat</h2>
          <div className="chat-box">
            {chatHistory.length === 0 ? (
              <p className="placeholder">Enter a prompt in the box below to begin.</p>
            ) : (
              chatHistory.map((item, idx) => (
                <div
                  key={`${item.role}-${idx}`}
                  className={`chat-line ${item.role}`}
                >
                  {item.text}
                </div>
              ))
            )}
          </div>
          <div className="chat-input">
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSend()
              }}
              title="Type a prompt and press Enter"
            />
            <button
              className="send"
              onClick={handleSend}
              disabled={loading}
              title="Send the prompt to the backend"
            >
              {loading ? 'Sending…' : 'Send'}
            </button>
          </div>
          {error && <div className="error">{error}</div>}
          <div className="chat-response">
            <div className="response-title">LLM Control Tower</div>
            <div className="response-body">
              {response || 'Response will appear here.'}
            </div>
          </div>
        </aside>

        <section className="panel center-panel">
          <div className="routing-row">
            <div className="routing-label">
              <span>Routing Mode:</span>
              <div className="routing-toggle">
                <button
                  type="button"
                  className={routingMode === 'cache_aware' ? 'active' : ''}
                  onClick={() => handleRoutingChange('cache_aware')}
                  title="Prefer workers that already cached this prompt"
                >
                  <span className="toggle-dot" />
                  <span>Cache Aware</span>
                </button>
                <button
                  type="button"
                  className={routingMode === 'least_queue' ? 'active' : ''}
                  onClick={() => handleRoutingChange('least_queue')}
                  title="Prefer the worker with the shortest queue"
                >
                  <span className="toggle-dot" />
                  <span>Least Queue</span>
                </button>
              </div>
            </div>
            <div className="actions-row">
              <button
                type="button"
                className={`pill-btn danger ${killWorker ? 'active' : ''}`}
                onClick={() => {
                  const next = !killWorker
                  setKillWorker(next)
                  updateState({ kill_worker: next })
                }}
                title="Toggle Worker A health (simulated)"
              >
                <span className="btn-icon">
                  <IconSkull />
                </span>
                <span>{killWorker ? 'Restore Worker' : 'Kill Worker'}</span>
              </button>
              <button
                type="button"
                className={`pill-btn warn ${delayYellow ? 'active' : ''}`}
                onClick={() => handleDelay(!delayYellow, false)}
                title="Add 2s latency to workers"
              >
                <span className="btn-icon">
                  <IconBolt />
                </span>
                <span>Inject 2s Latency</span>
              </button>
              <button
                type="button"
                className={`pill-btn hot ${delayRed ? 'active' : ''}`}
                onClick={() => handleDelay(false, !delayRed)}
                title="Add 2s latency and errors"
              >
                <span className="btn-icon">
                  <IconClock />
                </span>
                <span>Inject 2s Latency</span>
              </button>
              <button
                type="button"
                className={`pill-btn cool ${rateLimit ? 'active' : ''}`}
                onClick={() => {
                  const next = !rateLimit
                  setRateLimit(next)
                  updateState({ rate_limit: next ? 5 : 60 })
                }}
                title="Throttle requests to 5 per minute"
              >
                <span className="btn-icon">
                  <IconGauge />
                </span>
                <span>Rate Limit to 5 req/min</span>
              </button>
            </div>
            <div className="action-status">
              {killWorker
                ? 'Worker A is DOWN (toggle to restore)'
                : 'All workers healthy'}
            </div>
          </div>

          <div className="flight">
            <div className="flight-header">
              <h3>Live Request Flight Path</h3>
            </div>
            <div className="flight-canvas">
              <div className="node user">User</div>
              <div className="node gateway">Gateway</div>
              <div className="node worker">Worker {selectedWorker}</div>
              <div className="path path-user" />
              <div className="path path-gateway" />
              <div className="signal signal-1" />
              <div className="signal signal-2" />
              <div className="signal signal-3" />
            </div>
          </div>

          <div className="why">
            <h3>Why Worker {selectedWorker}?</h3>
            {why.length > 0 && (
              <div className="why-list">
                {why.map((item) => (
                  <div key={item.title} className="why-item">
                    <span>{item.title}</span>
                    <span className="why-note">{item.note}</span>
                    <span className="score">+{item.score}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="worker-detail">
            <h3>Worker {selectedWorker}</h3>
            <div className="worker-body">
              <div className="bot">
                <div className="bot-face">
                  <span />
                  <span />
                </div>
                <div className="bot-body" />
              </div>
              <div className="worker-stats">
                {selectedWorkerData ? (
                  <>
                    <div>
                      <strong>{selectedWorkerData.status}</strong>
                      <span>Queue: {selectedWorkerData.queue}</span>
                      <span>Errors: {selectedWorkerData.errors}</span>
                    </div>
                    <div className="cache-row">
                      <span>Cache Warmth</span>
                      <div className="bar">
                        <div
                          className="bar-fill"
                          style={{ width: `${selectedWorkerData.cache_warmth}%` }}
                        />
                      </div>
                    </div>
                  </>
                ) : (
                  <p className="placeholder">Send a request to see details.</p>
                )}
              </div>
            </div>
          </div>
        </section>

        <aside className="panel right-panel">
          <div className="observability-header">
            <h2>Observability</h2>
          </div>
          <div className="observability-list">
            {workers.length === 0 ? (
              <p className="placeholder">Send a request to see details.</p>
            ) : (
              workers.map((worker) => (
                <button
                  type="button"
                  key={worker.id}
                  className={`worker-card ${selectedWorker === worker.label ? 'selected' : ''}`}
                  onClick={() => setSelectedWorker(worker.label)}
                  title="Click to focus this worker"
                >
                  <div className="worker-card-header">
                    <h3>Worker {worker.label}</h3>
                    <span className={`status ${worker.status.toLowerCase()}`}>
                      {worker.status}
                    </span>
                  </div>
                  <div className="worker-card-body">
                    <div className="mini-bot">
                      <span />
                      <span />
                      <div className="mini-bot-mouth" />
                    </div>
                    <div className="worker-metrics">
                      <span>Queue: {worker.queue}</span>
                      <span>Errors: {worker.errors}</span>
                    </div>
                  </div>
                  <div className="cache-row">
                    <span>Cache Warmth</span>
                    <div className="bar">
                      <div
                        className="bar-fill"
                        style={{ width: `${worker.cache_warmth}%` }}
                      />
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}

export default App
