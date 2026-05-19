const MAP = {
  'Новый':       { bg: 'bg-blue-100',   text: 'text-blue-600' },
  'Подтверждён': { bg: 'bg-yellow-100', text: 'text-yellow-700' },
  'В пути':      { bg: 'bg-orange-100', text: 'text-orange-600' },
  'Доставлен':   { bg: 'bg-green-100',  text: 'text-green-600' },
  'Отменён':     { bg: 'bg-red-100',    text: 'text-red-500' },
  'Возврат':     { bg: 'bg-gray-100',   text: 'text-gray-500' },
}

export default function StatusBadge({ status }) {
  const s = MAP[status] || { bg: 'bg-gray-100', text: 'text-gray-400' }
  return (
    <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${s.bg} ${s.text}`}>
      {status || '—'}
    </span>
  )
}
