import { useEffect, useState } from 'react'
import { api } from '../api'
import OrderCard from '../components/OrderCard'
import ProductForm from '../components/ProductForm'
import StatusBadge from '../components/StatusBadge'

const TABS = ['Заказы', 'Статистика', 'Товары']

const STATUSES = ['Новый', 'Подтверждён', 'В пути', 'Доставлен', 'Отменён']

export default function AdminPage() {
  const [tab, setTab] = useState(0)
  const [orders, setOrders] = useState([])
  const [stats, setStats] = useState(null)
  const [products, setProducts] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editProduct, setEditProduct] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadOrders = () => api.getAllOrders().then(setOrders)
  const loadStats  = () => api.getStats().then(setStats)
  const loadProducts = () => api.getProducts().then(setProducts)

  useEffect(() => {
    Promise.all([loadOrders(), loadStats(), loadProducts()]).finally(() => setLoading(false))
  }, [])

  const changeStatus = async (id, status) => {
    await api.updateOrder(id, status)
    loadOrders()
  }

  const handleSaveProduct = async (data) => {
    if (editProduct !== null) {
      await api.updateProduct(editProduct, data)
    } else {
      await api.addProduct(data)
    }
    setShowForm(false)
    setEditProduct(null)
    loadProducts()
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#F5F5F5]">
      {/* Header */}
      <div className="bg-[#FFBE00] px-4 py-3 flex items-center gap-3 shadow">
        <img src="/logo.png" alt="SOOQ" className="w-10 h-10 rounded-xl" />
        <div>
          <p className="font-bold text-[#1A1A1A] text-base leading-none">Панель Админа</p>
          <p className="text-[10px] text-[#1A1A1A]/60 uppercase tracking-widest">SOOQ.TJ</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex bg-white border-b border-gray-100">
        {TABS.map((t, i) => (
          <button key={i} onClick={() => setTab(i)}
            className={`flex-1 py-2.5 text-xs font-semibold transition-all
              ${tab === i ? 'text-[#1A1A1A] border-b-2 border-[#FFBE00]' : 'text-gray-400'}`}>
            {t}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-3">

        {/* ЗАКАЗЫ */}
        {tab === 0 && (
          loading ? <div className="text-center py-16 text-gray-400">Загрузка...</div> :
          orders.length === 0 ? (
            <div className="text-center py-16 text-gray-400">Заказов нет</div>
          ) : (
            orders.map((o, i) => (
              <div key={i} className="bg-white rounded-2xl p-4 mb-3 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <p className="font-bold text-sm">#{o.id}</p>
                  <StatusBadge status={o.status} />
                </div>
                <p className="text-sm text-[#1A1A1A]">👤 {o.name} · 📱 {o.phone}</p>
                <p className="text-sm text-gray-500 mt-0.5">📦 {o.product_name} · 💰 {o.price} сом</p>
                <p className="text-xs text-gray-400 mt-0.5">📍 {o.address}</p>
                <p className="text-xs text-gray-300 mt-0.5">{o.timestamp}</p>
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {STATUSES.map(s => (
                    <button key={s} onClick={() => changeStatus(o.id, s)}
                      className={`text-xs px-2.5 py-1 rounded-full font-semibold transition-all
                        ${o.status === s
                          ? 'bg-[#FFBE00] text-[#1A1A1A]'
                          : 'bg-gray-100 text-gray-500 active:bg-[#FFBE00] active:text-[#1A1A1A]'}`}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ))
          )
        )}

        {/* СТАТИСТИКА */}
        {tab === 1 && (
          stats ? (
            <div className="grid grid-cols-2 gap-3 mt-1">
              {[
                { label: 'Сегодня заказов', value: stats.today_count },
                { label: 'Выручка сегодня', value: `${stats.today_sum} сом` },
                { label: 'За месяц заказов', value: stats.month_count },
                { label: 'Выручка за месяц', value: `${stats.month_sum} сом` },
                { label: 'Всего заказов', value: stats.total_count, wide: true },
              ].map((s, i) => (
                <div key={i} className={`bg-white rounded-2xl p-4 shadow-sm ${s.wide ? 'col-span-2' : ''}`}>
                  <p className="text-xs text-gray-400 mb-1">{s.label}</p>
                  <p className="text-2xl font-black text-[#FFBE00]">{s.value}</p>
                </div>
              ))}
            </div>
          ) : <div className="text-center py-16 text-gray-400">Загрузка...</div>
        )}

        {/* ТОВАРЫ */}
        {tab === 2 && (
          <div>
            <button onClick={() => { setEditProduct(null); setShowForm(true) }}
              className="w-full bg-[#FFBE00] text-[#1A1A1A] font-bold rounded-2xl py-3 text-sm mb-4 active:scale-95 transition-transform">
              + Добавить товар
            </button>

            {showForm && (
              <ProductForm
                initial={editProduct !== null ? products[editProduct] : null}
                onSave={handleSaveProduct}
                onCancel={() => { setShowForm(false); setEditProduct(null) }}
              />
            )}

            {products.map((p, i) => (
              <div key={i} className="bg-white rounded-2xl p-3 mb-2 flex gap-3 shadow-sm">
                {p['Фото (URL)'] && (
                  <img src={p['Фото (URL)']} className="w-16 h-16 rounded-xl object-cover flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm text-[#1A1A1A] line-clamp-1">
                    {p['Название (RU)'] || p['col2']}
                  </p>
                  <p className="text-xs text-gray-400">{p['Категория'] || p['col3']}</p>
                  <p className="text-sm font-bold text-[#FFBE00] mt-0.5">
                    {p['Продажная цена'] || p['col6']} сом
                  </p>
                </div>
                <button onClick={() => { setEditProduct(i); setShowForm(true) }}
                  className="text-xs text-gray-400 px-2 self-start mt-1">✏️</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
