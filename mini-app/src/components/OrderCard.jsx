import StatusBadge from './StatusBadge'

export default function OrderCard({ order: o }) {
  return (
    <div className="bg-white rounded-2xl p-4 mb-3 shadow-sm">
      <div className="flex justify-between items-start mb-2">
        <p className="font-bold text-sm text-[#1A1A1A]">#{o.id}</p>
        <StatusBadge status={o.status} />
      </div>
      <p className="text-sm text-gray-600">📦 {o.product_name}</p>
      <p className="text-sm font-bold text-[#FFBE00] mt-0.5">💰 {o.price} сомони</p>
      <p className="text-xs text-gray-400 mt-1">{o.timestamp}</p>
    </div>
  )
}
