import { useEffect, useState, useRef } from 'react'
import { api } from '../api'
import ProductForm from '../components/ProductForm'
import StatusBadge from '../components/StatusBadge'
import { useTelegram } from '../useTelegram'

const TABS = ['Заказы', 'Статистика', 'Товары', 'Настройки']
const STATUSES = ['Новый', 'Подтверждён', 'В пути', 'Доставлен', 'Отменён']

function photo(p) {
  return p['Фото (URL)'] || p['Фото 1'] || p['Фото'] || p['photo_url'] || ''
}
function name_(p)  { return p['Название (RU)'] || p['Название'] || p['col2'] || 'Товар' }
function price_(p) { return p['Продажная цена'] || p['Цена'] || p['col6'] || '—' }
function cat_(p)   { return p['Категория'] || p['col3'] || '' }

export default function AdminPage() {
  const { user } = useTelegram()
  const [tab, setTab] = useState(0)
  const [orders, setOrders] = useState([])
  const [stats, setStats] = useState(null)
  const [products, setProducts] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editProduct, setEditProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [logoUrl, setLogoUrl] = useState('/uploads/logo.png')
  const [logoUploading, setLogoUploading] = useState(false)
  const [logoOk, setLogoOk] = useState(false)
  const logoInputRef = useRef()

  const loadOrders   = () => api.getAllOrders().then(setOrders).catch(e => console.warn('orders:', e))
  const loadStats    = () => api.getStats().then(setStats).catch(e => console.warn('stats:', e))
  const loadProducts = () => api.getProducts().then(setProducts).catch(e => console.warn('products:', e))

  const loadAll = () => {
    setError('')
    return Promise.all([loadOrders(), loadStats(), loadProducts()])
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadAll() }, [])

  const changeStatus = async (id, status) => {
    try {
      await api.updateOrder(id, status)
      loadOrders()
    } catch (e) {
      console.warn('changeStatus:', e)
    }
  }

  const handleSaveProduct = async (data) => {
    try {
      if (editProduct !== null) {
        await api.updateProduct(editProduct, data)
      } else {
        await api.addProduct(data)
      }
      setShowForm(false)
      setEditProduct(null)
      loadProducts()
    } catch (e) {
      alert('Ошибка сохранения: ' + e.message)
    }
  }

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setLogoUploading(true)
    setLogoOk(false)
    try {
      const res = await api.uploadLogo(file)
      setLogoUrl(res.url + '?t=' + Date.now())
      setLogoOk(true)
    } catch (e) {
      alert('Ошибка загрузки: ' + e.message)
    } finally {
      setLogoUploading(false)
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#F5F5F5]">
      {/* Header */}
      <div className="bg-[#FFBE00] px-4 py-3 flex items-center gap-3 shadow">
        <img
          src={logoUrl}
          alt="SOOQ"
          className="w-10 h-10 rounded-xl object-cover"
          onError={e => { e.target.src = '/logo.svg' }}
        />
        <div className="flex-1">
          <p className="font-bold text-[#1A1A1A] text-base leading-none">Панель Админа</p>
          <p className="text-[10px] text-[#1A1A1A]/60 uppercase tracking-widest">
            {user?.first_name || 'SOOQ.TJ'}
          </p>
        </div>
        <button onClick={loadAll} className="text-[#1A1A1A]/60 text-xl px-2">↻</button>
      </div>

      {/* Tabs */}
      <div className="flex bg-white border-b border-gray-100 overflow-x-auto">
        {TABS.map((t, i) => (
          <button key={i} onClick={() => setTab(i)}
            className={`flex-1 py-2.5 text-xs font-semibold whitespace-nowrap px-2 transition-all
              ${tab === i ? 'text-[#1A1A1A] border-b-2 border-[#FFBE00]' : 'text-gray-400'}`}>
            {t}
          </button>
        ))}
      </div>

      {error && (
        <div className="mx-3 mt-3 bg-red-50 border border-red-200 rounded-xl p-3">
          <p className="text-xs text-red-500">⚠️ Ошибка: {error}</p>
          <button onClick={loadAll} className="text-xs text-red-600 font-bold mt-1">Повторить</button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3">

        {/* ЗАКАЗЫ */}
        {tab === 0 && (
          loading
            ? <div className="text-center py-16 text-gray-400">Загрузка...</div>
            : orders.length === 0
              ? <div className="text-center py-16 text-gray-400">
                  <p className="text-4xl mb-3">📋</p>
                  <p>Заказов пока нет</p>
                </div>
              : orders.map((o, i) => (
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
        )}

        {/* СТАТИСТИКА */}
        {tab === 1 && (
          loading
            ? <div className="text-center py-16 text-gray-400">Загрузка...</div>
            : !stats
              ? <div className="text-center py-16 text-gray-400">Нет данных</div>
              : <div className="grid grid-cols-2 gap-3 mt-1">
                  {[
                    { label: 'Заказов сегодня',   value: stats.today_count },
                    { label: 'Выручка сегодня',   value: `${stats.today_sum} сом` },
                    { label: 'За месяц заказов',  value: stats.month_count },
                    { label: 'Выручка за месяц',  value: `${stats.month_sum} сом` },
                    { label: 'Всего заказов',     value: stats.total_count, wide: true },
                  ].map((s, i) => (
                    <div key={i} className={`bg-white rounded-2xl p-4 shadow-sm ${s.wide ? 'col-span-2' : ''}`}>
                      <p className="text-xs text-gray-400 mb-1">{s.label}</p>
                      <p className="text-2xl font-black text-[#FFBE00]">{s.value}</p>
                    </div>
                  ))}
                </div>
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

            {loading
              ? <div className="text-center py-8 text-gray-400">Загрузка...</div>
              : products.length === 0
                ? <div className="text-center py-8 text-gray-400">Товаров нет</div>
                : products.map((p, i) => (
                    <div key={i} className="bg-white rounded-2xl p-3 mb-2 flex gap-3 shadow-sm">
                      {photo(p)
                        ? <img src={photo(p)} className="w-16 h-16 rounded-xl object-cover flex-shrink-0" onError={e => { e.target.style.display='none' }} />
                        : <div className="w-16 h-16 rounded-xl bg-gray-100 flex items-center justify-center text-2xl flex-shrink-0">📦</div>
                      }
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm text-[#1A1A1A] line-clamp-1">{name_(p)}</p>
                        <p className="text-xs text-gray-400">{cat_(p)}</p>
                        <p className="text-sm font-bold text-[#FFBE00] mt-0.5">{price_(p)} сом</p>
                      </div>
                      <button onClick={() => { setEditProduct(i); setShowForm(true) }}
                        className="text-xs text-gray-400 px-2 self-start mt-1">✏️</button>
                    </div>
                  ))
            }
          </div>
        )}

        {/* НАСТРОЙКИ */}
        {tab === 3 && (
          <div className="space-y-4">
            {/* Логотип */}
            <div className="bg-white rounded-2xl p-4 shadow-sm">
              <p className="font-bold text-sm text-[#1A1A1A] mb-3">Логотип магазина</p>
              <div className="flex items-center gap-4 mb-4">
                <img
                  src={logoUrl}
                  alt="Логотип"
                  className="w-20 h-20 rounded-2xl object-cover border-2 border-[#FFBE00]"
                  onError={e => { e.target.src = '/logo.svg' }}
                />
                <div>
                  <p className="text-xs text-gray-400 mb-2">Текущий логотип</p>
                  {logoOk && <p className="text-xs text-green-500 font-semibold">✅ Загружен!</p>}
                </div>
              </div>
              <input ref={logoInputRef} type="file" accept="image/*" className="hidden" onChange={handleLogoUpload} />
              <button
                onClick={() => logoInputRef.current?.click()}
                disabled={logoUploading}
                className="w-full bg-[#FFBE00] text-[#1A1A1A] font-bold rounded-xl py-3 text-sm active:scale-95 transition-transform disabled:opacity-60">
                {logoUploading ? 'Загружаем...' : '📷 Загрузить логотип'}
              </button>
              <p className="text-[10px] text-gray-400 mt-2 text-center">PNG / JPG / SVG · рекомендуется квадратный</p>
            </div>

            {/* Информация */}
            <div className="bg-white rounded-2xl p-4 shadow-sm">
              <p className="font-bold text-sm text-[#1A1A1A] mb-3">Информация</p>
              <div className="space-y-1.5">
                <p className="text-xs text-gray-400">Telegram ID: <span className="text-[#1A1A1A] font-mono font-semibold">{user?.id || '—'}</span></p>
                <p className="text-xs text-gray-400">Имя: <span className="text-[#1A1A1A] font-semibold">{user?.first_name || '—'}</span></p>
                <p className="text-xs text-gray-400">Роль: <span className="text-green-600 font-bold">✅ admin</span></p>
                <p className="text-xs text-gray-400">Товаров в каталоге: <span className="text-[#1A1A1A] font-semibold">{products.length}</span></p>
                <p className="text-xs text-gray-400">Всего заказов: <span className="text-[#1A1A1A] font-semibold">{orders.length}</span></p>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
