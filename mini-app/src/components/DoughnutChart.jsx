// SVG doughnut — 3 slices: profit (green), costOfGoods (gold), expenses (orange).
// Props: income (net profit), costOfGoods, expenses, size.
// Legacy 2-prop usage (income + expense) still works — expense maps to costOfGoods.

export default function DoughnutChart({
  income = 0,
  expense = 0,       // legacy prop — treated as costOfGoods if costOfGoods not passed
  costOfGoods,
  expenses: explicitExp = 0,
  size = 180,
}) {
  const cog  = costOfGoods !== undefined ? costOfGoods : expense
  const profit = Math.max(0, income)
  // chart only shows profit + explicit expenses (cog excluded from slices)
  const chartTotal = profit + explicitExp || 1
  const revenue    = profit + cog + explicitExp  // shown in center

  const r      = size / 2
  const stroke = size * 0.18
  const innerR = r - stroke / 2
  const c      = 2 * Math.PI * innerR

  const profitDash = (profit      / chartTotal) * c
  const expDash    = (explicitExp / chartTotal) * c
  const cogDash    = 0  // kept for legacy compat, not rendered

  return (
    <div className="relative inline-flex" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        {/* track */}
        <circle cx={r} cy={r} r={innerR} fill="none"
          stroke="#1F2937" strokeOpacity="0.12" strokeWidth={stroke} />

        {/* доп. расходы — оранжевый */}
        {explicitExp > 0 && (
          <circle cx={r} cy={r} r={innerR} fill="none"
            stroke="#F97316"
            strokeWidth={stroke}
            strokeDasharray={`${expDash} ${c}`}
            strokeDashoffset={0}
            strokeLinecap="butt" />
        )}
        {/* прибыль — зелёный */}
        {profit > 0 && (
          <circle cx={r} cy={r} r={innerR} fill="none"
            stroke="#22C55E"
            strokeWidth={stroke}
            strokeDasharray={`${profitDash} ${c}`}
            strokeDashoffset={-expDash}
            strokeLinecap="butt" />
        )}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <p className="text-[9px] uppercase font-black tracking-widest text-gray-400 dark:text-gray-500">Выручка</p>
        <p className="font-black text-lg leading-none mt-0.5 text-[#0A0A0A] dark:text-white">
          {Math.round(revenue)}
        </p>
        <p className="text-[9px] font-bold text-gray-400 dark:text-gray-500 mt-0.5">сом</p>
      </div>
    </div>
  )
}
