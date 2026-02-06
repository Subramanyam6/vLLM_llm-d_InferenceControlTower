import http from 'k6/http'
import { check } from 'k6'
import { Counter } from 'k6/metrics'

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
const workerSelectedA = new Counter('worker_selected_a')
const workerSelectedB = new Counter('worker_selected_b')
const workerSelectedC = new Counter('worker_selected_c')
const workerSelectedD = new Counter('worker_selected_d')
const workerSelectedE = new Counter('worker_selected_e')
const workerSelectedOther = new Counter('worker_selected_other')
const workerSelectedMissing = new Counter('worker_selected_missing')

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
    if (parsed && parsed.error) {
      failedRequests.add(1)
      failureReasonInvalidJson.add(1)
      return
    }
    const workerLabel = String(parsed?.selected_worker || '').trim().toUpperCase()
    if (!workerLabel) {
      workerSelectedMissing.add(1)
    } else if (workerLabel === 'A') {
      workerSelectedA.add(1)
    } else if (workerLabel === 'B') {
      workerSelectedB.add(1)
    } else if (workerLabel === 'C') {
      workerSelectedC.add(1)
    } else if (workerLabel === 'D') {
      workerSelectedD.add(1)
    } else if (workerLabel === 'E') {
      workerSelectedE.add(1)
    } else {
      workerSelectedOther.add(1)
    }
  } catch (error) {
    failedRequests.add(1)
    failureReasonInvalidJson.add(1)
    return
  }

  successfulRequests.add(1)
}
