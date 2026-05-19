import { useState } from 'react'
import PhotoUpload from './PhotoUpload'

export default function ProductForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState({
    name:      initial?.['Название (RU)'] || initial?.['col2'] || '',
    category:  initial?.['Категория']      || initial?.['col3'] || '',
    photo_url: initial?.['Фото (URL)'] || initial?.['Фото 1'] || initial?.['Фото'] || '',
    price:     initial?.['Продажная цена'] || initial?.['col6'] || '',
    qty:       initial?.['В наличии (шт)'] || initial?.['col9'] || '',
  })

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = () => {
    if (!form.name || !form.price) return alert('Заполните название и цену')
    onSave({ ...form, price: parseFloat(form.price), qty: parseInt(form.qty) || 0 })
  }

  return (
    <div className="bg-[#FFBE00]/10 border border-[#FFBE00] rounded-2xl p-4 mb-4">
      <p className="font-bold text-[#1A1A1A] mb-3 text-sm">
        {initial ? 'Редактировать товар' : 'Новый товар'}
      </p>

      <PhotoUpload value={form.photo_url} onChange={v => setForm(f => ({ ...f, photo_url: v }))} />

      <input placeholder="Название товара *" value={form.name} onChange={set('name')}
        className="w-full mt-2 bg-white rounded-xl px-3 py-2.5 text-sm outline-none border border-gray-100" />
      <input placeholder="Категория" value={form.category} onChange={set('category')}
        className="w-full mt-2 bg-white rounded-xl px-3 py-2.5 text-sm outline-none border border-gray-100" />
      <div className="flex gap-2 mt-2">
        <input placeholder="Цена (сом) *" type="number" value={form.price} onChange={set('price')}
          className="flex-1 bg-white rounded-xl px-3 py-2.5 text-sm outline-none border border-gray-100" />
        <input placeholder="Кол-во" type="number" value={form.qty} onChange={set('qty')}
          className="w-24 bg-white rounded-xl px-3 py-2.5 text-sm outline-none border border-gray-100" />
      </div>

      <div className="flex gap-2 mt-3">
        <button onClick={onCancel}
          className="flex-1 bg-white border border-gray-200 text-gray-500 font-semibold text-sm rounded-xl py-2.5 active:scale-95 transition-transform">
          Отмена
        </button>
        <button onClick={handleSubmit}
          className="flex-1 bg-[#1A1A1A] text-white font-bold text-sm rounded-xl py-2.5 active:scale-95 transition-transform">
          Сохранить
        </button>
      </div>
    </div>
  )
}
