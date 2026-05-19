import { useEffect, useState } from 'react'
import { useTelegram } from './useTelegram'
import { api, setInitData, setUserId } from './api'
import ClientPage from './pages/ClientPage'
import AdminPage from './pages/AdminPage'
import DriverPage from './pages/DriverPage'

export default function App() {
  const { ready, expand, initData } = useTelegram()
  const [role, setRole] = useState(null)

  useEffect(() => {
    ready()
    expand()
    setInitData(initData)
    setUserId(user.id)
    api.getMe()
      .then(u => setRole(u.role))
      .catch(() => setRole('client'))
  }, [])

  if (!role) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#F5F5F5]">
      <img src="/uploads/logo.png" alt="SOOQ" className="w-24 h-24 animate-pulse mb-3 rounded-2xl object-cover" onError={e => { e.target.src = '/logo.svg' }} />
      <p className="font-bold text-xl text-[#1A1A1A]">SOOQ.TJ</p>
      <p className="text-sm text-gray-400 mt-1">Загрузка...</p>
    </div>
  )

  if (role === 'admin')  return <AdminPage />
  if (role === 'driver') return <DriverPage />
  return <ClientPage />
}
