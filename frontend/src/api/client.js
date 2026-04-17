import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// Attach JWT token to every request automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to /auth on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/auth'
    }
    return Promise.reject(err)
  }
)

// ── Scans ──────────────────────────────────────────────────────
export const createScan = (payload) =>
  api.post('/scans', payload).then((r) => r.data)

export const uploadScan = (formData) =>
  api.post('/scans/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)

export const listScans = (params = {}) =>
  api.get('/scans', { params }).then((r) => r.data)

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
  const ext = format === 'html' ? 'html' : format === 'pdf' ? 'pdf' : 'json'
  const mime = format === 'pdf' ? 'application/pdf' : format === 'html' ? 'text/html' : 'application/json'
  const url = window.URL.createObjectURL(new Blob([response.data], { type: mime }))
  const a = document.createElement('a')
  a.href = url
  a.download = `trustify-report-${scanId.slice(0, 8)}.${ext}`
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

// ── GitHub ─────────────────────────────────────────────────────
export const listGithubRepos = () =>
  api.get('/auth/github/repos').then((r) => r.data)

export default api
