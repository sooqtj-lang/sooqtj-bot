import { useEffect, useState } from 'react'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'

const STATUSES = ['В пути', 'Доставлен', 'Возврат']

export default function DriverPage() {
  const [deliveries, setDeliveries] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () =>
    api.getDeliveries().then(setDeliveries).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const changeStatus = async (id, status) => {
    await api.updateOrder(id, status)
    load()
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#F5F5F5]">
      {/* Header */}
      <div className="bg-[#FFBE00] px-4 py-3 flex items-center gap-3 shadow">
        <img src="/logo.svg" alt="SOOQ" className="w-10 h-10 rounded-xl" />
        <div>
          <p className="font-bold text-[#1A1A1A] text-base leading-none">Мои Доставки</p>
          <p className="text-[10px] text-[#1A1A1A]/60 uppercase tracking-widest">SOOQ.TJ</p>
        </div>
        <button onClick={load} className="ml-auto text-[#1A1A1A]/60 text-xl">↻</button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {loading ? (
          <div className="text-center py-16 text-gray-400">Загрузка...</div>
        ) : deliveries.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-3">✅</p>
            <p>Нет активных доставок</p>
          </div>
        ) : (
          deliveries.map((d, i) => (
            <div key={i} className="bg-white rounded-2xl p-4 mb-3 shadow-sm">
              <div className="flex justify-between items-start mb-3">
                <p className="font-bold text-base">#{d.id}</p>
                <StatusBadge status={d.status} />
              </div>
              <div className="space-y-1 mb-4">
                <p className="text-sm font-semibold">👤 {d.name}</p>
                <p className="text-sm text-gray-500">📱 {d.phone}</p>
                <p className="text-sm text-gray-500">📍 {d.address}</p>
                <p className="text-sm text-gray-500">📦 {d.product_name}</p>
                <p className="text-sm font-bold text-[#FFBE00]">💰 {d.price} сомони</p>
              </div>
              <div className="flex gap-2">
                {STATUSES.map(s => (
                  <button key={s} onClick={() => changeStatus(d.id, s)}
                    className={`flex-1 text-xs py-2 rounded-xl font-semibold transition-all
                      ${d.status === s
                        ? 'bg-[#FFBE00] text-[#1A1A1A]'
                        : 'bg-[#F5F5F5] text-gray-500 active:bg-[#FFBE00] active:text-[#1A1A1A]'}`}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
