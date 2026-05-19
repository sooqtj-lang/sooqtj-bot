import { useEffect, useState } from 'react'
import { api } from '../api'
import { useTelegram } from '../useTelegram'
import ProductCard from '../components/ProductCard'
import OrderCard from '../components/OrderCard'

const TABS = ['Каталог', 'Корзина', 'Мои заказы']

export default function ClientPage() {
  const { user } = useTelegram()
  const [tab, setTab] = useState(0)
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ name: '', phone: '', address: '' })
  const [placing, setPlacing] = useState(false)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    api.getProducts().then(setProducts).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (tab === 2) api.getMyOrders().then(setOrders)
  }, [tab])

  const addToCart = (p) => {
    setCart(prev => {
      const exist = prev.find(i => i._index === p._index)
      if (exist) return prev.map(i => i._index === p._index ? { ...i, qty: i.qty + 1 } : i)
      return [...prev, { ...p, qty: 1 }]
    })
  }

  const removeFromCart = (idx) => setCart(prev => prev.filter(i => i._index !== idx))
  const cartTotal = cart.reduce((s, i) => s + parseFloat(i['Продажная цена'] || 0) * i.qty, 0)

  const placeOrder = async () => {
    if (!form.name || !form.phone || !form.address) return alert('Заполните все поля')
    setPlacing(true)
    for (const item of cart) {
      await api.createOrder({
        name: form.name,
        phone: form.phone,
        address: form.address,
        product_id: item._index?.toString() || '',
        product_name: item['Название (RU)'] || item['col2'] || 'Товар',
        quantity: item.qty,
        price: parseFloat(item['Продажная цена'] || item['col6'] || 0) * item.qty,
      })
    }
    setCart([])
    setSuccess(true)
    setPlacing(false)
    setTimeout(() => { setSuccess(false); setTab(2) }, 2000)
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#F5F5F5]">
      {/* Header */}
      <div className="bg-[#FFBE00] px-4 py-3 flex items-center gap-3 shadow">
        <img src="/logo.png" alt="SOOQ" className="w-10 h-10 rounded-xl" />
        <div>
          <p className="font-bold text-[#1A1A1A] text-base leading-none">SOOQ.TJ</p>
          <p className="text-[10px] text-[#1A1A1A]/60 uppercase tracking-widest">Online Shopping</p>
        </div>
        {cart.length > 0 && tab !== 1 && (
          <button onClick={() => setTab(1)}
            className="ml-auto bg-[#1A1A1A] text-white text-xs font-bold px-3 py-1.5 rounded-full">
            🛒 {cart.length}
          </button>
        )}
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
        {/* КАТАЛОГ */}
        {tab === 0 && (
          loading ? (
            <div className="flex justify-center py-16 text-gray-400">Загрузка...</div>
          ) : products.length === 0 ? (
            <div className="text-center py-16 text-gray-400">Каталог пуст</div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {products.map((p, i) => (
                <ProductCard key={i} product={p} onAdd={() => addToCart(p)} />
              ))}
            </div>
          )
        )}

        {/* КОРЗИНА */}
        {tab === 1 && (
          <div>
            {cart.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <p className="text-4xl mb-3">🛒</p>
                <p>Корзина пуста</p>
              </div>
            ) : (
              <>
                {cart.map((item, i) => (
                  <div key={i} className="bg-white rounded-2xl p-3 mb-2 flex items-center gap-3 shadow-sm">
                    {item['Фото (URL)'] && (
                      <img src={item['Фото (URL)']} className="w-14 h-14 rounded-xl object-cover" />
                    )}
                    <div className="flex-1">
                      <p className="font-semibold text-sm text-[#1A1A1A] line-clamp-1">
                        {item['Название (RU)'] || item['col2']}
                      </p>
                      <p className="text-xs text-gray-400">{item['Продажная цена'] || item['col6']} сом × {item.qty}</p>
                    </div>
                    <button onClick={() => removeFromCart(item._index)} className="text-red-400 text-lg">✕</button>
                  </div>
                ))}

                <div className="bg-[#FFBE00] rounded-2xl p-4 mt-4">
                  <p className="font-bold text-[#1A1A1A] text-base mb-3">Итого: {cartTotal} сомони</p>
                  <input placeholder="Ваше имя" value={form.name}
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    className="w-full bg-white rounded-xl px-3 py-2 text-sm mb-2 outline-none" />
                  <input placeholder="Номер телефона" value={form.phone}
                    onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                    className="w-full bg-white rounded-xl px-3 py-2 text-sm mb-2 outline-none" />
                  <input placeholder="Адрес доставки" value={form.address}
                    onChange={e => setForm(f => ({ ...f, address: e.target.value }))}
                    className="w-full bg-white rounded-xl px-3 py-2 text-sm mb-3 outline-none" />
                  {success ? (
                    <div className="bg-[#1A1A1A] text-white text-center rounded-xl py-3 font-bold">
                      ✅ Заказ оформлен!
                    </div>
                  ) : (
                    <button onClick={placeOrder} disabled={placing}
                      className="w-full bg-[#1A1A1A] text-white font-bold rounded-xl py-3 text-sm active:scale-95 transition-transform">
                      {placing ? 'Оформляем...' : '📦 Оформить заказ'}
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* МОИ ЗАКАЗЫ */}
        {tab === 2 && (
          <div>
            {orders.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <p className="text-4xl mb-3">📦</p>
                <p>Заказов пока нет</p>
              </div>
            ) : (
              orders.map((o, i) => <OrderCard key={i} order={o} />)
            )}
          </div>
        )}
      </div>
    </div>
  )
}
