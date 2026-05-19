import { useEffect, useState } from 'react'
import { useTelegram } from './useTelegram'
import { setInitData, setUserId } from './api'
import ClientPage from './pages/ClientPage'
import AdminPage from './pages/AdminPage'
import DriverPage from './pages/DriverPage'

const BASE = import.meta.env.VITE_API_URL || ''

export default function App() {
  const { ready, expand, initData, user } = useTelegram()
  const [role, setRole] = useState(null)

  useEffect(() => {
    ready()
    expand()
    setInitData(initData)

    // uid from URL (?uid=...) is most reliable — set by bot
    const params = new URLSearchParams(window.location.search)
    const urlUid = parseInt(params.get('uid') || '0')
    const tgUid = user?.id || 0
    const userId = urlUid || tgUid

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
    </div>
  )

  if (role === 'admin')  return <AdminPage />
  if (role === 'driver') return <DriverPage onLogout={() => setRole('client')} />
  return <ClientPage />
}
