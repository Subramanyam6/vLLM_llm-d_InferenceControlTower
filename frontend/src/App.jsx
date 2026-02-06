import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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

const GatewayTower = ({ size = 220, className = '' }) => (
  <div className={className} style={{ width: size, height: size }}>
    <svg
      width="100%"
      height="100%"
      viewBox="0 0 220 220"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Control tower"
    >
      <defs>
        <linearGradient id="gGlass" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#CBE2F3" />
          <stop offset="0.55" stopColor="#9EC0DD" />
          <stop offset="1" stopColor="#6E98B8" />
        </linearGradient>
        <linearGradient id="gRoof" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#4B667A" />
          <stop offset="1" stopColor="#2A3F50" />
        </linearGradient>
        <linearGradient id="gBody" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#6C8FA8" />
          <stop offset="1" stopColor="#3D5D73" />
        </linearGradient>
        <clipPath id="bandClip">
          <path d="M74 78 L146 78 L141 104 L79 104 Z" />
        </clipPath>
        <filter id="soft" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="0.6" result="b" />
          <feColorMatrix
            in="b"
            type="matrix"
            values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.45 0"
            result="bb"
          />
          <feMerge>
            <feMergeNode in="bb" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <g>
        <rect x="102" y="134" width="16" height="62" rx="3" fill="#2A3B49" stroke="#1A232B" strokeWidth="3" />

        <path
          d="M68 70 L152 70 L145 110 L137 110 L137 130 L83 130 L83 110 L75 110 Z"
          fill="url(#gBody)"
          stroke="#1A232B"
          strokeWidth="3"
          strokeLinejoin="round"
        />

        <path
          d="M74 78 L146 78 L141 104 L79 104 Z"
          fill="#3A5567"
          stroke="#1A232B"
          strokeWidth="3"
          strokeLinejoin="round"
        />

        <rect x="79" y="109" width="62" height="24" rx="0" fill="#3A5567" stroke="#1A232B" strokeWidth="3" />

        <g filter="url(#soft)" clipPath="url(#bandClip)">
          <path
            d="M74 78 L92 78 L94.5 104 L79 104 Z"
            fill="url(#gGlass)"
            stroke="#1A232B"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path
            d="M92 78 L110 78 L110 104 L94.5 104 Z"
            fill="url(#gGlass)"
            stroke="#1A232B"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path
            d="M110 78 L128 78 L125.5 104 L110 104 Z"
            fill="url(#gGlass)"
            stroke="#1A232B"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path
            d="M128 78 L146 78 L141 104 L125.5 104 Z"
            fill="url(#gGlass)"
            stroke="#1A232B"
            strokeWidth="2"
            strokeLinejoin="round"
          />
        </g>

        <g filter="url(#soft)">
          <rect x="83" y="113" width="54" height="20" rx="0" fill="url(#gGlass)" stroke="#1A232B" strokeWidth="3" />
          <line x1="101" y1="113" x2="101" y2="133" stroke="#1A232B" strokeWidth="3" />
          <line x1="119" y1="113" x2="119" y2="133" stroke="#1A232B" strokeWidth="3" />
        </g>

        <path
          d="M64 62 L156 62 L152 72 L68 72 Z"
          fill="#2C4354"
          stroke="#1A232B"
          strokeWidth="3"
          strokeLinejoin="round"
        />

        <path
          d="M74 44 L146 44 L156 62 L64 62 Z"
          fill="url(#gRoof)"
          stroke="#1A232B"
          strokeWidth="3"
          strokeLinejoin="round"
        />

        <rect x="80" y="52" width="26" height="8" rx="2" fill="#C9585A" stroke="#1A232B" strokeWidth="2.4" />
        <rect x="108" y="52" width="10" height="8" rx="2" fill="#D79057" stroke="#1A232B" strokeWidth="2.4" />
        <rect x="120" y="52" width="26" height="8" rx="2" fill="#5BC2C2" stroke="#1A232B" strokeWidth="2.4" />

        <rect x="108.6" y="22" width="2.8" height="24" rx="1.4" fill="#2E3E4B" />
        <circle cx="110" cy="18" r="10" fill="#CFD6DF" stroke="#1A232B" strokeWidth="3" />

        <rect x="78" y="204" width="64" height="16" rx="6" fill="#2C3A46" stroke="#1A232B" strokeWidth="3" />
        <rect x="88" y="198" width="44" height="10" rx="4" fill="#3A4B5A" stroke="#1A232B" strokeWidth="3" />
      </g>
    </svg>
  </div>
)

const resolveMode = (rawMode, disableGrpc, enableLlmd) => {
  const nextMode =
    rawMode === 'LLMD' || rawMode === 'llm-d (local)' || rawMode === 'SGLANG' || rawMode === 'sglang (local)'
      ? 'LLMD'
      : rawMode === 'GRPC' || rawMode === 'gRPC (local)'
        ? 'GRPC'
        : 'SIM'

  if (disableGrpc && nextMode === 'GRPC') return 'SIM'
  if (!enableLlmd && nextMode === 'LLMD') return 'SIM'
  return nextMode
}

const FLIGHT_POINTS = {
  user: { x: 12, y: 84 },
  gateway: { x: 42, y: 82 },
  workerCardX: 84,
  workerPacketX: 74,
}

const workerLabelFromIndex = (idx) => String.fromCharCode(65 + idx)

const workerLaneY = (index, total) => {
  if (total <= 1) return 46
  const minY = 24
  const maxY = 70
  return minY + ((maxY - minY) * index) / (total - 1)
}

const statusClassName = (status) => String(status || 'pending').toLowerCase()

const STRESS_RESULTS_BUTTON_DATE = '02/06/2026'
const INTERNAL_PILL_GAP_MS = 1000
const DUMMY_HINT = ' (dummy - host locally to use original tools)'

const buildInternalPillSteps = (mode, workerLabel = '') => {
  const suffix = mode === 'SIM' ? DUMMY_HINT : ''
  if (mode === 'LLMD') {
    return [
      `SGLang preprocessing${suffix}`,
      `Routing policy scoring${suffix}`,
      `llm-d gateway handoff${suffix}`,
      workerLabel ? `Dispatching to Worker ${workerLabel}${suffix}` : `Selecting worker${suffix}`,
    ]
  }
  if (mode === 'GRPC') {
    return [
      `Prompt normalization${suffix}`,
      `Routing policy scoring${suffix}`,
      `gRPC backend handoff${suffix}`,
      workerLabel ? `Dispatching to Worker ${workerLabel}${suffix}` : `Selecting worker${suffix}`,
    ]
  }
  return [
    `Prompt normalization${suffix}`,
    `Routing policy scoring${suffix}`,
    `Simulation handoff${suffix}`,
    workerLabel ? `Dispatching to Worker ${workerLabel}${suffix}` : `Selecting worker${suffix}`,
  ]
}

const toPct = (num) => `${(Number(num || 0) * 100).toFixed(2)}%`

const runDurationSec = (startedAt, endedAt) => {
  const startTs = Date.parse(startedAt || '')
  const endTs = Date.parse(endedAt || '')
  if (!Number.isFinite(startTs) || !Number.isFinite(endTs)) return null
  const seconds = Math.round((endTs - startTs) / 1000)
  return seconds > 0 ? seconds : null
}

function App() {
  const initialMode = import.meta.env.VITE_BACKEND || 'SIM'
  const disableGrpc = ['1', 'true', 'yes'].includes(
    String(import.meta.env.VITE_DISABLE_GRPC || '').toLowerCase(),
  )
  const enableLlmd = ['1', 'true', 'yes'].includes(
    String(import.meta.env.VITE_ENABLE_LLMD || '').toLowerCase(),
  )
  const lockMode = ['1', 'true', 'yes'].includes(
    String(import.meta.env.VITE_LOCK_MODE || '').toLowerCase(),
  )
  const normalizedMode = initialMode === 'Light-weight Demo' ? 'SIM' : initialMode
  const [mode, setMode] = useState(() => resolveMode(normalizedMode, disableGrpc, enableLlmd))
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
  const [flightStage, setFlightStage] = useState('idle')
  const [flightTargetWorker, setFlightTargetWorker] = useState('')
  const [flightPacket, setFlightPacket] = useState({
    visible: false,
    x: FLIGHT_POINTS.user.x,
    y: FLIGHT_POINTS.user.y,
    tone: 'uplink',
  })
  const [lastMeta, setLastMeta] = useState({
    requestId: '',
    latencyMs: null,
    cacheHit: null,
    worker: '',
    workerIdentity: '',
  })
  const [showStressResults, setShowStressResults] = useState(false)
  const [stressResults, setStressResults] = useState(null)
  const [stressLoading, setStressLoading] = useState(false)
  const [stressError, setStressError] = useState('')
  const [flightProcessPill, setFlightProcessPill] = useState({
    label: 'Waiting for a request.',
    tone: 'idle',
  })
  const [lastFlightReplay, setLastFlightReplay] = useState(null)
  const flightTimers = useRef([])
  const flightStartedAtRef = useRef(0)
  const isSim = mode === 'SIM'
  const cacheLabel = isSim ? 'Cache Warmth' : 'Cache Warmth (Light-weight Demo only)'
  const selectedWorkerData =
    workers.find((worker) => worker.label === selectedWorker) || workers[0]
  const flightWorkers = useMemo(() => {
    if (workers.length > 0) {
      return workers.map((worker, idx) => ({
        id: worker.id,
        label: worker.label,
        status: worker.status || 'UNKNOWN',
        queue: worker.queue,
        errors: worker.errors,
        cache_warmth: worker.cache_warmth,
        y: workerLaneY(idx, workers.length),
      }))
    }

    const fallbackCount = Math.max(1, scale)
    return Array.from({ length: fallbackCount }, (_, idx) => ({
      id: idx,
      label: workerLabelFromIndex(idx),
      status: 'PENDING',
      queue: null,
      errors: null,
      cache_warmth: null,
      y: workerLaneY(idx, fallbackCount),
    }))
  }, [workers, scale])
  const flightWorkerLabels = flightWorkers.map((worker) => worker.label)
  const selectedFlightWorker = flightWorkerLabels.includes(selectedWorker)
    ? selectedWorker
    : (flightWorkerLabels[0] || 'A')
  const highlightedFlightWorker = flightTargetWorker || selectedFlightWorker
  const isUplinkActive = flightStage !== 'idle'
  const isDownlinkActive = flightStage === 'downlink' || flightStage === 'error'

  const clearFlightTimers = useCallback(() => {
    flightTimers.current.forEach((timerId) => clearTimeout(timerId))
    flightTimers.current = []
  }, [])

  const resolveFlightTarget = useCallback((workerLabel, candidateLabels) => {
    const labels =
      Array.isArray(candidateLabels) && candidateLabels.length > 0
        ? candidateLabels
        : flightWorkerLabels.length > 0
          ? flightWorkerLabels
          : ['A']
    const requestedIndex = labels.findIndex((label) => label === workerLabel)
    const index = requestedIndex >= 0 ? requestedIndex : 0
    const targetLabel = labels[index]
    const targetWorker = flightWorkers.find((worker) => worker.label === targetLabel)
    return {
      label: targetLabel,
      x: FLIGHT_POINTS.workerPacketX,
      y: targetWorker ? targetWorker.y : workerLaneY(index, labels.length),
    }
  }, [flightWorkerLabels, flightWorkers])

  const animateUplink = useCallback(() => {
    clearFlightTimers()
    flightStartedAtRef.current = Date.now()
    setFlightStage('uplink')
    setFlightTargetWorker('')
    const steps = buildInternalPillSteps(mode)
    setFlightProcessPill({
      label: steps[0],
      tone: 'active',
    })
    setFlightPacket({
      visible: true,
      x: FLIGHT_POINTS.user.x,
      y: FLIGHT_POINTS.user.y,
      tone: 'uplink',
    })
    const uplinkHop = setTimeout(() => {
      setFlightPacket({
        visible: true,
        x: FLIGHT_POINTS.gateway.x,
        y: FLIGHT_POINTS.gateway.y,
        tone: 'uplink',
      })
    }, 120)
    flightTimers.current.push(uplinkHop)
    for (let idx = 1; idx <= 2 && idx < steps.length; idx += 1) {
      const updateStep = setTimeout(() => {
        setFlightProcessPill({
          label: steps[idx],
          tone: 'active',
        })
      }, INTERNAL_PILL_GAP_MS * idx)
      flightTimers.current.push(updateStep)
    }
  }, [clearFlightTimers, mode])

  const animateDownlink = useCallback((workerLabel, candidateLabels, failed = false) => {
    const target = resolveFlightTarget(workerLabel, candidateLabels)
    clearFlightTimers()
    setFlightStage(failed ? 'error' : 'downlink')
    setFlightTargetWorker(target.label)
    setFlightPacket({
      visible: true,
      x: FLIGHT_POINTS.gateway.x,
      y: FLIGHT_POINTS.gateway.y,
      tone: failed ? 'error' : 'downlink',
    })
    const workerHop = setTimeout(() => {
      setFlightPacket({
        visible: true,
        x: target.x,
        y: target.y,
        tone: failed ? 'error' : 'downlink',
      })
      setFlightProcessPill({
        label: failed
          ? `Worker ${target.label} returned an error.`
          : `Worker ${target.label} accepted the request.`,
        tone: failed ? 'error' : 'done',
      })
    }, 120)
    const settle = setTimeout(() => {
      setFlightStage('idle')
      setFlightPacket((prev) => ({ ...prev, visible: false }))
    }, 860)
    const resetPill = setTimeout(() => {
      setFlightProcessPill({
        label: 'Waiting for a request.',
        tone: 'idle',
      })
    }, 2200)
    flightTimers.current.push(workerHop)
    flightTimers.current.push(settle)
    flightTimers.current.push(resetPill)
  }, [clearFlightTimers, resolveFlightTarget])

  const queueDownlink = useCallback((workerLabel, candidateLabels, failed = false) => {
    const target = resolveFlightTarget(workerLabel, candidateLabels)
    setFlightTargetWorker(target.label)
    const steps = buildInternalPillSteps(mode, target.label)
    const elapsed = Date.now() - flightStartedAtRef.current
    const dispatchStepIdx = steps.length - 1
    const dispatchAtMs = INTERNAL_PILL_GAP_MS * dispatchStepIdx
    const delayToDispatchStep = Math.max(0, dispatchAtMs - elapsed)
    const showDispatchStep = setTimeout(() => {
      setFlightProcessPill({
        label: steps[dispatchStepIdx],
        tone: failed ? 'error' : 'active',
      })
    }, delayToDispatchStep)
    const downlinkTimer = setTimeout(() => {
      animateDownlink(target.label, candidateLabels, failed)
    }, delayToDispatchStep + INTERNAL_PILL_GAP_MS)
    flightTimers.current.push(showDispatchStep)
    flightTimers.current.push(downlinkTimer)
  }, [animateDownlink, mode, resolveFlightTarget])

  const applyControlState = useCallback((data) => {
    if (!data) return
    if (typeof data.scale === 'number') setScale(data.scale)
    if (typeof data.routing_mode === 'string') setRoutingMode(data.routing_mode)
    if (typeof data.kill_worker === 'boolean') setKillWorker(data.kill_worker)

    const delayValue = typeof data.delay_s === 'number' ? data.delay_s : null
    const errorRateValue = typeof data.error_rate === 'number' ? data.error_rate : null
    if (delayValue !== null || errorRateValue !== null) {
      const isRedDelay = (errorRateValue ?? 0) > 0
      const isYellowDelay = (delayValue ?? 0) >= 2 && !isRedDelay
      setDelayYellow(isYellowDelay)
      setDelayRed(isRedDelay)
    }

    if (typeof data.rate_limit === 'number') setRateLimit(data.rate_limit <= 5)
    if (typeof data.backend === 'string') {
      setMode(resolveMode(data.backend, disableGrpc, enableLlmd))
    }
    if (typeof data.selected_worker === 'string') setSelectedWorker(data.selected_worker)
    if (Array.isArray(data.why)) setWhy(data.why)
    if (Array.isArray(data.workers_detail)) setWorkers(data.workers_detail)
    if (typeof data.scale_status === 'string') setScaleStatus(data.scale_status)
    if (Object.prototype.hasOwnProperty.call(data, 'scale_error')) {
      setScaleError(typeof data.scale_error === 'string' ? data.scale_error : '')
    }
  }, [disableGrpc, enableLlmd])

  useEffect(() => {
    const loadState = async () => {
      try {
        const res = await fetch('/api/state')
        if (!res.ok) return
        const data = await res.json()
        applyControlState(data)
      } catch {
        // ignore
      }
    }
    loadState()
  }, [applyControlState])

  useEffect(() => {
    if (workers.length === 0) return
    const isStillAvailable = workers.some((worker) => worker.label === selectedWorker)
    if (!isStillAvailable) {
      setSelectedWorker(workers[0].label)
    }
  }, [workers, selectedWorker])

  useEffect(() => {
    if (flightStage !== 'idle') return
    setFlightTargetWorker(selectedFlightWorker)
  }, [flightStage, selectedFlightWorker])

  useEffect(() => () => clearFlightTimers(), [clearFlightTimers])

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
      applyControlState(data)
    } catch {
      setError('Could not reach the API server.')
    }
  }

  const handleSend = async () => {
    if (loading) return
    if (!prompt.trim()) {
      setError('Please enter a prompt.')
      return
    }
    animateUplink()
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
      applyControlState(data)
      const responseLabels =
        Array.isArray(data.workers_detail) && data.workers_detail.length > 0
          ? data.workers_detail.map((worker) => worker.label)
          : flightWorkerLabels
      const routedWorker =
        typeof data.selected_worker === 'string' && data.selected_worker
          ? data.selected_worker
          : selectedFlightWorker
      const failed = !res.ok || Boolean(data.error)
      setLastFlightReplay({
        worker: routedWorker,
        labels: responseLabels,
        failed,
      })
      queueDownlink(routedWorker, responseLabels, failed)
      setLastMeta({
        requestId: data.request_id || '',
        latencyMs: typeof data.latency_ms === 'number' ? data.latency_ms : null,
        cacheHit:
          typeof data.cache_hit === 'boolean' || data.cache_hit === null
            ? data.cache_hit
            : null,
        worker: data.selected_worker || '',
        workerIdentity: data.worker_identity || '',
      })
      if (typeof data.mode === 'string') {
        setMode(resolveMode(data.mode, disableGrpc, enableLlmd))
      }
      setChatHistory((prev) => [
        ...prev,
        { role: 'user', text: prompt },
        { role: 'assistant', text: data.text || '' },
      ])
      setPrompt('')
    } catch {
      setLastFlightReplay({
        worker: selectedFlightWorker,
        labels: flightWorkerLabels,
        failed: true,
      })
      queueDownlink(selectedFlightWorker, flightWorkerLabels, true)
      setError('Could not reach the API server.')
    } finally {
      setLoading(false)
    }
  }

  const handleReplayFlight = () => {
    if (!lastFlightReplay || loading) return
    animateUplink()
    queueDownlink(
      lastFlightReplay.worker,
      lastFlightReplay.labels,
      lastFlightReplay.failed,
    )
  }

  const handleModeChange = (nextMode) => {
    if (disableGrpc && nextMode === 'GRPC') return
    if (!enableLlmd && nextMode === 'LLMD') return
    if (lockMode && nextMode !== mode) return
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

  const loadStressResults = useCallback(async () => {
    setStressLoading(true)
    setStressError('')
    try {
      const tryUrls = ['/api/stress/latest', '/stress/latest.json']
      let loaded = null
      let reportMissing = false
      for (const url of tryUrls) {
        try {
          const res = await fetch(url)
          const data = await res.json().catch(() => ({}))
          if (res.ok && !data.error) {
            loaded = data
            break
          }
          if (data?.error === 'no_stress_report_found') {
            reportMissing = true
          }
        } catch {
          // try next source
        }
      }
      if (!loaded) {
        setStressResults(null)
        setStressError(
          reportMissing
            ? 'No stress report found yet. Run scripts/run_stress.sh first.'
            : 'Unable to load stress report. If API was just updated, restart local services.',
        )
        return
      }
      const normalized = { ...loaded }
      if (!normalized.run_id && normalized.source_file) {
        const match = String(normalized.source_file).match(/load\/([^/]+)\//)
        if (match?.[1]) {
          normalized.run_id = match[1]
        }
      }
      setStressResults(normalized)
    } catch {
      // ignore
    } finally {
      setStressLoading(false)
    }
  }, [])

  const handleStressToggle = () => {
    const next = !showStressResults
    setShowStressResults(next)
    if (next) loadStressResults()
  }

  const modeLabel =
    mode === 'SIM'
      ? 'Light-weight Demo'
      : mode === 'LLMD'
        ? 'llm-d (local)'
          : 'gRPC (local)'
  const scaleLabel =
    scaleStatus === 'error'
      ? `Scale failed${scaleError ? `: ${scaleError}` : ''}`
      : scaleStatus === 'ok'
        ? mode === 'LLMD'
          ? 'Scaled in Kubernetes (llm-d)'
          : 'Scaled in Kubernetes'
        : 'Local scale'
  const hostedTitle = disableGrpc
    ? 'Hosted (Light-weight Demo)'
    : 'Light-weight Demo (no local services)'
  const hostedNote = disableGrpc
    ? 'Runs in hosted mode with dummy Python functions that mimic routing and worker behavior.'
    : 'No local services required. This Light-weight Demo uses dummy Python functions to mimic backend behavior.'
  const stressAttempts = Number(stressResults?.requests_attempted || 0)
  const stressSuccess = Number(stressResults?.requests_succeeded || 0)
  const stressFailed = Number(stressResults?.requests_failed || 0)
  const stressErrorRate = Number(stressResults?.error_rate || 0)
  const stressDurationSec = runDurationSec(stressResults?.started_at, stressResults?.ended_at)
  const stressSuccessRate = stressAttempts > 0
    ? (stressSuccess / stressAttempts) * 100
    : 0
  const stressWorkerDistribution = ['A', 'B', 'C', 'D', 'E'].map((label) => ({
    label,
    count: Number(stressResults?.worker_distribution?.[label] || 0),
    pct: Number(stressResults?.worker_distribution_pct?.[label] || 0),
  }))
  const renderRobotSvg = (idPrefix) => (
    <svg
      className="robot-svg"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 256 256"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={`${idPrefix}-bodyG`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#2e3b3a" />
          <stop offset="1" stopColor="#141a1a" />
        </linearGradient>
        <linearGradient id={`${idPrefix}-faceG`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2b2f2f" />
          <stop offset="1" stopColor="#151818" />
        </linearGradient>
        <filter id={`${idPrefix}-glowG`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <circle cx="128" cy="30" r="8" fill="#8ff7b5" filter={`url(#${idPrefix}-glowG)`} />
      <rect x="124" y="36" width="8" height="22" rx="4" fill="#3b4a49" />

      <rect
        x="66"
        y="55"
        width="124"
        height="98"
        rx="28"
        fill={`url(#${idPrefix}-faceG)`}
        stroke="#2b3232"
        strokeWidth="6"
      />
      <rect
        x="84"
        y="76"
        width="88"
        height="56"
        rx="18"
        fill="#0e1414"
        stroke="#2a2f2f"
        strokeWidth="4"
      />

      <g filter={`url(#${idPrefix}-glowG)`}>
        <rect x="104" y="95" width="18" height="16" rx="6" fill="#8ff7b5" />
        <rect x="134" y="95" width="18" height="16" rx="6" fill="#8ff7b5" />
      </g>
      <rect x="114" y="118" width="28" height="6" rx="3" fill="#243030" />

      <path
        d="M66 102c-12 2-18 12-18 24v6c0 12 6 22 18 24"
        fill="none"
        stroke="#2b3232"
        strokeWidth="10"
        strokeLinecap="round"
      />
      <path
        d="M190 102c12 2 18 12 18 24v6c0 12-6 22-18 24"
        fill="none"
        stroke="#2b3232"
        strokeWidth="10"
        strokeLinecap="round"
      />
      <rect x="42" y="110" width="18" height="36" rx="8" fill="#1b2323" stroke="#2b3232" strokeWidth="4" />
      <rect x="196" y="110" width="18" height="36" rx="8" fill="#1b2323" stroke="#2b3232" strokeWidth="4" />

      <rect
        x="74"
        y="150"
        width="108"
        height="76"
        rx="26"
        fill={`url(#${idPrefix}-bodyG)`}
        stroke="#2b3232"
        strokeWidth="6"
      />
      <rect
        x="96"
        y="168"
        width="64"
        height="18"
        rx="9"
        fill="#0e1414"
        stroke="#2a2f2f"
        strokeWidth="4"
      />
      <circle cx="106" cy="204" r="6" fill="#2a2f2f" />
      <circle cx="150" cy="204" r="6" fill="#2a2f2f" />

      <rect x="156" y="158" width="18" height="18" rx="6" fill="#0e1414" stroke="#2a2f2f" strokeWidth="3" />
      <circle cx="165" cy="167" r="4" fill="#8ff7b5" filter={`url(#${idPrefix}-glowG)`} />

      <rect x="92" y="218" width="26" height="22" rx="8" fill="#1b2323" stroke="#2b3232" strokeWidth="4" />
      <rect x="138" y="218" width="26" height="22" rx="8" fill="#1b2323" stroke="#2b3232" strokeWidth="4" />
      <rect x="88" y="236" width="34" height="10" rx="5" fill="#0e1414" stroke="#2a2f2f" strokeWidth="3" />
      <rect x="134" y="236" width="34" height="10" rx="5" fill="#0e1414" stroke="#2a2f2f" strokeWidth="3" />
    </svg>
  )

  const todayLabel = new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date())

  return (
    <div className="shell">
      <header className="topbar">
        <div className="title-block">
          <div className="title-icon" />
          <div>
            <h1>LLM Inference Control Tower</h1>
            <p className="subtitle">Mode: {modeLabel}</p>
          </div>
        </div>
        <div className="wip-note">
          <span className="wip-pill">WIP</span>
          <span>Actively evolving · {todayLabel}</span>
        </div>
        <div className="mode-switch">
          <span>Mode</span>
          <div className="mode-toggle">
            <button
              type="button"
              className={mode === 'SIM' ? 'active' : ''}
              title="Run the local simulated worker pool"
              disabled={lockMode && mode !== 'SIM'}
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
              disabled={(lockMode && mode !== 'GRPC') || disableGrpc}
              onClick={() => handleModeChange('GRPC')}
            >
              gRPC
            </button>
            <button
              type="button"
              className={`${mode === 'LLMD' ? 'active' : ''}${enableLlmd ? '' : ' disabled'}`}
              title={
                enableLlmd
                  ? 'Use the local llm-d gateway (simulated vLLM)'
                  : 'LLM-D is available in local runs only.'
              }
              disabled={(lockMode && mode !== 'LLMD') || !enableLlmd}
              onClick={() => handleModeChange('LLMD')}
            >
              LLM-D (local)
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
            title="Number of workers (SIM) or replicas (gRPC/LLM-D)"
          />
          <div className="ticks">
            {[1, 2, 3, 4, 5].map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
          <div className={`scale-status ${scaleStatus}`}>
            {scaleLabel}
          </div>
        </div>
      </header>

      <section className="info-card">
        <div className="info-icon" aria-hidden="true">
          i
        </div>
        <div className="info-content">
          <div className="info-title">Project Snapshot</div>
          <div className="info-split">
            <div className="info-block hosted">
              <div className="info-block-title">{hostedTitle}</div>
              <ul className="info-list">
                <li>{hostedNote}</li>
                <li>This path is for UX/demo flow and observability storytelling, not real backend traffic.</li>
                <li>Send prompts, see routing decisions, and simulate latency/rate limits.</li>
                <li>Observe worker health, queues, and cache warmth.</li>
              </ul>
            </div>
            <div className="info-block local">
              <div className="info-block-title">Local-Only (requires setup)</div>
              <ul className="info-list">
                <li>gRPC backend mode with real workers.</li>
                <li>llm-d gateway mode (set <code>VITE_ENABLE_LLMD=1</code>).</li>
                <li>
                  SGLang pre-route for llm-d (set <code>ENABLE_SGLANG_FRONT=1</code>):
                  rewrites prompts first, then forwards to llm-d.
                </li>
                <li>
                  SGLang endpoint for this stage: <code>SGLANG_HTTP_URL</code>{' '}
                  (OpenAI chat API format).
                </li>
                <li>vLLM dev image via OpenAI HTTP (set <code>VLLM_HTTP_URL</code>).</li>
                <li>Kubernetes scaling + service-mesh routing.</li>
                <li>Local gateway + mesh for true backend traffic.</li>
              </ul>
              {lockMode && (
                <div className="info-note">
                  Mode is locked for this run to prevent misrouted traffic.
                </div>
              )}
            </div>
          </div>
          <ul className="info-list info-meta">
            <li>
              <strong>What it is:</strong> A control tower UI + gateway that
              routes LLM requests across workers with cache-aware, queue-aware
              logic.
            </li>
            <li>
              <strong>Tech:</strong> React (Vite) UI, Python gateway, gRPC
              simulator, SGLang pre-route, vLLM OpenAI HTTP, Docker, K8s/Istio
              hooks, and OTEL console export.
            </li>
            <li>
              <strong>llm-d / vLLM mimic:</strong> Worker selection, retries,
              rate limits, and observability patterns without a full GPU
              cluster. Optional llm-d local mode routes through an llm-d
              gateway (Kubernetes namespace <code>llm-d</code>) using the
              official <code>llm-d-inference-sim</code> image. gRPC mode runs
              in the llm-d mesh (<code>llm-d-mesh</code>) with a local
              inference-sim image built from <code>Dockerfile.grpc-server</code>.
              Can also target a local vLLM dev image via{' '}
              <code>VLLM_HTTP_URL</code>.
            </li>
            <li>
              <strong>SGLang stage behavior:</strong> When enabled in local
              llm-d mode, the gateway sends your prompt to SGLang first to
              rewrite it into a concise downstream instruction, then forwards
              that rewritten prompt to llm-d. Hosted HF mode stays SIM-only, so
              this stage is intentionally disabled there.
            </li>
            <li>
              <strong>Tools (hosted/local):</strong> Hosted via Docker (HF
              Spaces), local workflows use Docker, kubectl, Istio, and kind
              for mesh demos.
            </li>
          </ul>
          <div className="stress-results">
            <button
              type="button"
              className={`stress-results-btn${showStressResults ? ' open' : ''}`}
              onClick={handleStressToggle}
            >
              Stress Test {STRESS_RESULTS_BUTTON_DATE}
            </button>
            {showStressResults && (
              <div className="stress-results-panel">
                {stressLoading && <p className="stress-plain">Loading latest report…</p>}
                {!stressLoading && stressError && (
                  <p className="stress-plain">{stressError}</p>
                )}
                {!stressLoading && !stressError && stressResults && (
                  <>
                    <div className="stress-run-label">
                      llm-d report: {stressResults.profile || 'custom'} · {stressResults.run_id || 'latest'}
                    </div>
                    <div className="stress-kpi-grid">
                      <div className="stress-kpi-card">
                        <span>Chat requests</span>
                        <strong>{stressAttempts.toLocaleString()}</strong>
                      </div>
                      <div className="stress-kpi-card">
                        <span>Success rate</span>
                        <strong>{stressSuccessRate.toFixed(2)}%</strong>
                      </div>
                      <div className="stress-kpi-card">
                        <span>Throughput</span>
                        <strong>{Number(stressResults.throughput_rps || 0).toFixed(1)} req/s</strong>
                      </div>
                      <div className="stress-kpi-card">
                        <span>p95 latency</span>
                        <strong>{Number(stressResults?.latency_ms?.p95 || 0).toFixed(3)} ms</strong>
                      </div>
                    </div>
                    <p className="stress-plain">
                      This card reads values directly from <code>{stressResults.source_file || 'reports/load/*/results.json'}</code>.
                    </p>
                    <p className="stress-plain">
                      In this run, llm-d handled {stressAttempts.toLocaleString()} requests with {stressFailed.toLocaleString()} failures ({toPct(stressErrorRate)} error rate).
                    </p>
                    <p className="stress-plain">
                      The worker split below is what this llm-d run reported for 5 workers A-E (Wondering why Worker A gets so many hits).
                    </p>
                    <div className="stress-worker-grid">
                      {stressWorkerDistribution.map((item) => (
                        <div key={item.label} className="stress-worker-card">
                          <span>Worker {item.label}</span>
                          <strong>{item.count.toLocaleString()}</strong>
                          <em>{item.pct.toFixed(2)}%</em>
                        </div>
                      ))}
                    </div>
                    <div className="stress-footer">
                      Window: {stressDurationSec !== null ? `${stressDurationSec}s` : 'n/a'} • Failed: {stressFailed.toLocaleString()} • p50/p99: {Number(stressResults?.latency_ms?.p50 || 0).toFixed(3)} ms / {Number(stressResults?.latency_ms?.p99 || 0).toFixed(3)} ms
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

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
                if (e.key === 'Enter' && !loading) handleSend()
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
            <div className="response-meta">
              <span>Worker: {lastMeta.worker || '—'}</span>
              <span>Backend identity: {lastMeta.workerIdentity || '—'}</span>
              <span>Cache hit: {lastMeta.cacheHit === true ? 'Yes' : lastMeta.cacheHit === false ? 'No' : 'N/A'}</span>
              <span>Latency: {lastMeta.latencyMs !== null ? `${lastMeta.latencyMs} ms` : '—'}</span>
              <span>Request: {lastMeta.requestId || '—'}</span>
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
                <span>Inject 2s + Errors</span>
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
              <h3>Simulated Request Flight Path</h3>
              <button
                type="button"
                className="flight-replay-btn"
                onClick={handleReplayFlight}
                disabled={!lastFlightReplay || loading}
                title="Replay the most recent request path"
              >
                Replay
              </button>
              <p className="flight-subtitle">
                User → Gateway → Worker {highlightedFlightWorker}
              </p>
            </div>
            <div className="flight-canvas">
              <GatewayTower size={164} className="flight-tower" />
              <div className={`node user${isUplinkActive ? ' active' : ''}`}>User</div>
              <div className={`node gateway${isUplinkActive ? ' active' : ''}`}>Gateway</div>
              <div className="flight-process" aria-live="polite">
                <div className={`flight-process-pill ${flightProcessPill.tone}`}>
                  {flightProcessPill.label}
                </div>
              </div>
              {flightWorkers.map((worker) => {
                const isFocused = worker.label === selectedFlightWorker
                const isRouteTarget = worker.label === highlightedFlightWorker
                const robotPrefix = `robot-lane-${worker.id}`
                const cachePercent = isSim && typeof worker.cache_warmth === 'number'
                  ? worker.cache_warmth
                  : null
                return (
                  <button
                    type="button"
                    key={worker.label}
                    className={`flight-worker-lane${isFocused ? ' focused' : ''}${isRouteTarget ? ' target' : ''}${isDownlinkActive && isRouteTarget ? ' active' : ''}${flightStage === 'error' && isRouteTarget ? ' error' : ''}`}
                    style={{ top: `${worker.y}%`, left: `${FLIGHT_POINTS.workerCardX}%` }}
                    onClick={() => setSelectedWorker(worker.label)}
                    title={`Focus Worker ${worker.label}`}
                  >
                    <div className="lane-robot">
                      {renderRobotSvg(robotPrefix)}
                    </div>
                    <div className="lane-body">
                      <div className="lane-head">
                        <span>Worker {worker.label}</span>
                        <span className={`status ${statusClassName(worker.status)}`}>
                          {worker.status}
                        </span>
                      </div>
                      <div className="lane-metrics">
                        <span>Q {worker.queue ?? '—'}</span>
                        <span>E {worker.errors ?? '—'}</span>
                        {cachePercent !== null && <span>C {cachePercent}%</span>}
                      </div>
                    </div>
                  </button>
                )
              })}
              {flightPacket.visible && (
                <div
                  className={`flight-packet ${flightPacket.tone}`}
                  style={{ left: `${flightPacket.x}%`, top: `${flightPacket.y}%` }}
                  aria-hidden="true"
                />
              )}
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
                {renderRobotSvg('robot-main')}
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
                      <span>{cacheLabel}</span>
                      <div className="bar">
                        <div
                          className="bar-fill"
                          style={{ width: `${isSim ? selectedWorkerData.cache_warmth : 0}%` }}
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
      </div>
    </div>
  )
}

export default App
