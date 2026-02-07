import http from 'k6/http'
import { check } from 'k6'
import { Counter, Trend } from 'k6/metrics'

const rate = Number(__ENV.RATE || 100)
const duration = __ENV.DURATION || '60s'
const preAllocatedVUs = Number(__ENV.VUS || 25)
const maxVUs = Number(__ENV.MAX_VUS || Math.max(preAllocatedVUs * 2, preAllocatedVUs + 10))

const successfulRequests = new Counter('successful_requests')
const failedRequests = new Counter('failed_requests')
const failureReason4xx = new Counter('failure_reason_http_4xx')
const failureReason5xx = new Counter('failure_reason_http_5xx')
const failureReasonNetwork = new Counter('failure_reason_network')
const failureReasonInvalidJson = new Counter('failure_reason_invalid_json')
const failureReasonApiError = new Counter('failure_reason_api_error')
const workerLabels = ['A', 'B', 'C', 'D', 'E']
const genericIdentityValues = new Set(['grpc', 'llm-d', 'sglang', 'vllm', 'vllm_http'])
const workerSelected = {}
const workerLatency = {}
const workerCacheHit = {}
const workerCacheMiss = {}
const workerCacheUnknown = {}
const workerResponseError = {}
const workerQueue = {}
const workerReportedErrors = {}
const workerReportedP95 = {}
const workerCacheWarmth = {}
for (const label of workerLabels) {
  const suffix = label.toLowerCase()
  workerSelected[label] = new Counter(`worker_selected_${suffix}`)
  workerLatency[label] = new Trend(`worker_latency_${suffix}`, true)
  workerCacheHit[label] = new Counter(`worker_cache_hit_${suffix}`)
  workerCacheMiss[label] = new Counter(`worker_cache_miss_${suffix}`)
  workerCacheUnknown[label] = new Counter(`worker_cache_unknown_${suffix}`)
  workerResponseError[label] = new Counter(`worker_response_error_${suffix}`)
  workerQueue[label] = new Trend(`worker_queue_${suffix}`)
  workerReportedErrors[label] = new Trend(`worker_reported_errors_${suffix}`)
  workerReportedP95[label] = new Trend(`worker_reported_p95_ms_${suffix}`, true)
  workerCacheWarmth[label] = new Trend(`worker_cache_warmth_${suffix}`)
}
const workerSelectedOther = new Counter('worker_selected_other')
const workerSelectedMissing = new Counter('worker_selected_missing')
const workerIdentityKnown = new Counter('worker_identity_known')
const workerIdentityMissing = new Counter('worker_identity_missing')
const workerIdentityGeneric = new Counter('worker_identity_generic')

function normalizeWorkerLabel(value) {
  const workerLabel = String(value || '').trim().toUpperCase()
  return workerLabels.includes(workerLabel) ? workerLabel : ''
}

function isLightWeightDemoMode(modeValue) {
  const value = String(modeValue || '').trim().toLowerCase()
  return value.includes('light-weight demo') || value === 'sim'
}

export const options = {
  scenarios: {
    submit_flow: {
      executor: 'constant-arrival-rate',
      rate,
      timeUnit: '1s',
      duration,
      preAllocatedVUs,
      maxVUs,
    },
  },
}

export default function () {
  const url = __ENV.API_URL || 'http://127.0.0.1:8000/api/submit'
  const backend = __ENV.BACKEND || 'LLMD'
  const routingMode = __ENV.ROUTING_MODE || 'least_queue'
  const payload = JSON.stringify({
    prompt: `stress prompt ${__VU}-${__ITER}`,
    backend,
    routing_mode: routingMode,
    scale: Number(__ENV.SCALE || 5),
    kill_worker: false,
    delay_s: 0,
    error_rate: 0,
    rate_limit: Number(__ENV.RATE_LIMIT || 1000000),
  })
  const params = {
    headers: { 'Content-Type': 'application/json' },
    timeout: __ENV.REQUEST_TIMEOUT || '120s',
  }

  let res
  try {
    res = http.post(url, payload, params)
  } catch (error) {
    failedRequests.add(1)
    failureReasonNetwork.add(1)
    return
  }

  const status = Number(res.status || 0)
  const ok = check(res, {
    'submit status is 2xx': (response) => response.status >= 200 && response.status < 300,
  })

  if (!ok) {
    failedRequests.add(1)
    if (status >= 400 && status < 500) {
      failureReason4xx.add(1)
    } else if (status >= 500) {
      failureReason5xx.add(1)
    } else {
      failureReasonNetwork.add(1)
    }
    return
  }

  try {
    const parsed = res.json()
    const modeValue = String(parsed?.mode || '').trim()
    const backendValue = String(parsed?.backend || backend || '').trim().toUpperCase()
    const isSimMode = isLightWeightDemoMode(modeValue) || backendValue === 'SIM'
    let workerLabel = normalizeWorkerLabel(parsed?.selected_worker)
    const workerIdentity = String(parsed?.worker_identity || '').trim()
    const hasConcreteIdentity =
      workerIdentity !== '' && !genericIdentityValues.has(workerIdentity.toLowerCase())

    if (!workerIdentity) {
      workerIdentityMissing.add(1)
    } else {
      workerIdentityKnown.add(1)
      if (genericIdentityValues.has(workerIdentity.toLowerCase())) {
        workerIdentityGeneric.add(1)
      }
    }

    // For llm-d/grpc paths, do not trust selected_worker if upstream identity is absent.
    if (!isSimMode && !hasConcreteIdentity) {
      workerLabel = ''
    }

    if (parsed && parsed.error) {
      failedRequests.add(1)
      failureReasonApiError.add(1)
      if (workerLabel) {
        workerResponseError[workerLabel].add(1)
      }
      return
    }
    if (!workerLabel) {
      workerSelectedMissing.add(1)
    } else {
      const durationMs = Number(res?.timings?.duration || 0)
      workerSelected[workerLabel].add(1)
      if (Number.isFinite(durationMs) && durationMs >= 0) {
        workerLatency[workerLabel].add(durationMs)
      }
      if (parsed?.cache_hit === true) {
        workerCacheHit[workerLabel].add(1)
      } else if (parsed?.cache_hit === false) {
        workerCacheMiss[workerLabel].add(1)
      } else {
        workerCacheUnknown[workerLabel].add(1)
      }
    }

    const workerDetails = Array.isArray(parsed?.workers_detail) ? parsed.workers_detail : []
    for (const detail of workerDetails) {
      const detailLabel = normalizeWorkerLabel(detail?.label)
      if (!detailLabel) continue
      const queueLen = Number(detail?.queue)
      const errorsSeen = Number(detail?.errors)
      const p95Seen = Number(detail?.p95_ms)
      const cacheWarmthSeen = Number(detail?.cache_warmth)
      if (Number.isFinite(queueLen)) workerQueue[detailLabel].add(queueLen)
      if (Number.isFinite(errorsSeen)) workerReportedErrors[detailLabel].add(errorsSeen)
      if (Number.isFinite(p95Seen)) workerReportedP95[detailLabel].add(p95Seen)
      if (Number.isFinite(cacheWarmthSeen)) workerCacheWarmth[detailLabel].add(cacheWarmthSeen)
    }

    if (workerLabel === '' && parsed?.selected_worker) {
      workerSelectedOther.add(1)
    }
  } catch (error) {
    failedRequests.add(1)
    failureReasonInvalidJson.add(1)
    return
  }

  successfulRequests.add(1)
}
