import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// ── Scans ──────────────────────────────────────────────────────
export const createScan = (payload) =>
  api.post('/scans', payload).then((r) => r.data)

export const uploadScan = (formData) =>
  api.post('/scans/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)

export const listScans = (skip = 0, limit = 20) =>
  api.get('/scans', { params: { skip, limit } }).then((r) => r.data)

export const getScan = (id) =>
  api.get(`/scans/${id}`).then((r) => r.data)

export const deleteScan = (id) =>
  api.delete(`/scans/${id}`)

// ── Findings ───────────────────────────────────────────────────
export const getFindings = (scanId, params = {}) =>
  api.get(`/findings/${scanId}`, { params }).then((r) => r.data)

// ── Reports ────────────────────────────────────────────────────
export const getReportUrl = (scanId, format = 'html') =>
  `/api/findings/${scanId}/report?format=${format}`

export const downloadReport = async (scanId, format = 'json') => {
  const response = await api.get(`/findings/${scanId}/report`, {
    params: { format },
    responseType: 'blob',
  })
  const ext = format === 'html' ? 'html' : 'json'
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = `trustify-report-${scanId.slice(0, 8)}.${ext}`
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export default api
