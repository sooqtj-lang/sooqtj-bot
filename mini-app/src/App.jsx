import { useEffect, useState } from 'react'
import { useTelegram } from './useTelegram'
import { setInitData, setUserId } from './api'
import ClientPage from './pages/ClientPage'
import AdminPage from './pages/AdminPage'
import DriverPage from './pages/DriverPage'

const BASE = import.meta.env.VITE_API_URL || ''

function getUid(user) {
  // 1. ?uid= из URL — самый надёжный (бот всегда проставляет)
  const params = new URLSearchParams(window.location.search)
  const urlUid = parseInt(params.get('uid') || '0')
  if (urlUid > 0) return urlUid

  // 2. Telegram initDataUnsafe.user.id
  const tgUid = user?.id || 0
  if (tgUid > 0) return tgUid

  return 0
}

export default function App() {
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
