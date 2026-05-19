import { useEffect, useState, Component } from 'react'
import { useTelegram } from './useTelegram'
import { setInitData, setUserId } from './api'
import ClientPage from './pages/ClientPage'
import AdminPage from './pages/AdminPage'
import DriverPage from './pages/DriverPage'

const BASE = import.meta.env.VITE_API_URL || ''

// ─── Error Boundary ──────────────────────────────────────────
class ErrorBoundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(e) { return { error: e } }
  render() {
    if (this.state.error) return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#F5F5F5] p-6">
        <p className="text-4xl mb-3">⚠️</p>
        <p className="font-bold text-[#1A1A1A] text-lg mb-2">Что-то пошло не так</p>
        <p className="text-xs text-gray-400 text-center mb-4">{String(this.state.error)}</p>
        <button onClick={() => window.location.reload()}
          className="bg-[#FFBE00] text-[#1A1A1A] font-bold px-6 py-2.5 rounded-full text-sm">
          Перезагрузить
        </button>
      </div>
    )
    return this.props.children
  }
}

// ─── UID detection ────────────────────────────────────────────
// Приоритет: URL ?uid= > localStorage > Telegram initDataUnsafe
function getUid(user) {
  // 1. ?uid= из URL — приходит когда пользователь нажимает кнопку в боте
  const params = new URLSearchParams(window.location.search)
  const urlUid = parseInt(params.get('uid') || '0')
  if (urlUid > 0) {
    // Запоминаем в localStorage чтобы следующее открытие тоже работало
    try { localStorage.setItem('sooq_uid', String(urlUid)) } catch (_) {}
    return urlUid
  }

  // 2. Telegram initDataUnsafe.user.id
  const tgUid = user?.id || 0
  if (tgUid > 0) {
    try { localStorage.setItem('sooq_uid', String(tgUid)) } catch (_) {}
    return tgUid
  }

  // 3. Запомненный из прошлой сессии (когда Telegram открывает без ?uid=)
  try {
    const stored = parseInt(localStorage.getItem('sooq_uid') || '0')
    if (stored > 0) return stored
  } catch (_) {}

  return 0
}

// ─── Main App ─────────────────────────────────────────────────
function AppInner() {
  const { ready, expand, initData, user } = useTelegram()
  const [role, setRole] = useState(null)
  const [detectedUid, setDetectedUid] = useState(0)

  useEffect(() => {
    ready()
    expand()
    setInitData(initData)

    const userId = getUid(user)
    setDetectedUid(userId)
    setUserId(userId)

    if (!userId) {
      setRole('client')
      return
    }

    fetch(`${BASE}/api/role?user_id=${userId}`)
      .then(r => r.json())
      .then(d => setRole(d.role || 'client'))
      .catch(() => setRole('client'))
  }, [])

  if (!role) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#F5F5F5]">
      <img
        src="/uploads/logo.png"
        alt="SOOQ"
        className="w-24 h-24 animate-pulse mb-3 rounded-2xl object-cover"
        onError={e => { e.target.src = '/logo.svg' }}
      />
      <p className="font-bold text-xl text-[#1A1A1A]">SOOQ.TJ</p>
      <p className="text-sm text-gray-400 mt-1">Загрузка...</p>
      {detectedUid > 0 && (
        <p className="text-[10px] text-gray-300 mt-1">uid: {detectedUid}</p>
      )}
    </div>
  )

  if (role === 'admin')  return <AdminPage />
  if (role === 'driver') return <DriverPage onLogout={() => setRole('client')} />
  return <ClientPage />
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppInner />
    </ErrorBoundary>
  )
}
