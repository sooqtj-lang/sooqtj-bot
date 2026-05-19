export default function ProductCard({ product: p, onAdd }) {
  const name  = p['Название (RU)'] || p['Название'] || p['col2'] || 'Товар'
  const price = p['Продажная цена'] || p['Цена'] || p['col6'] || '—'
  const photo = p['Фото (URL)'] || p['Фото 1'] || p['Фото'] || p['photo_url'] || null
  const cat   = p['Категория'] || p['col3'] || ''
  const qty   = parseInt(p['В наличии (шт)'] || p['В наличии'] || p['col9'] || '0')

  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-sm flex flex-col">
      {photo
        ? <img src={photo} alt={name} className="w-full h-32 object-cover" />
        : <div className="w-full h-32 bg-[#F5F5F5] flex items-center justify-center text-4xl">📦</div>
      }
      <div className="p-2.5 flex flex-col flex-1">
        {cat && <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">{cat}</p>}
        <p className="text-xs font-semibold text-[#1A1A1A] line-clamp-2 flex-1">{name}</p>
        <p className="text-sm font-black text-[#FFBE00] mt-1">{price} сом</p>
        <p className="text-[10px] text-gray-300 mb-2">{qty > 0 ? `В наличии: ${qty}` : 'Нет в наличии'}</p>
        <button
          onClick={onAdd}
          disabled={qty === 0}
          className="w-full bg-[#FFBE00] disabled:bg-gray-100 disabled:text-gray-300
            text-[#1A1A1A] font-bold text-xs rounded-xl py-2 active:scale-95 transition-transform">
          {qty > 0 ? '+ В корзину' : 'Нет'}
        </button>
      </div>
    </div>
  )
}
