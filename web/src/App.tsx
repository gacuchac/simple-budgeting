import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis } from 'recharts'
import { Doughnut, Line as CjLine } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, LineElement, PointElement, LinearScale, CategoryScale, type Plugin } from 'chart.js'
import { pie as d3pie, arc as d3arc } from 'd3-shape'
import { donut, CASES, series } from './model'

ChartJS.register(ArcElement, LineElement, PointElement, LinearScale, CategoryScale)
const q = new URLSearchParams(location.search)
const v = q.get('v') || 'a', c = q.get('case') || 'over', n = Number(q.get('n') || 31)
const model = donut(...CASES[c])
const MARK_W = 4 // degrees

function Empty() { return <p id="empty">No income or expenses in this period</p> }

function RechartsDonut() {
  if (model.kind === 'empty') return <Empty />
  const m = model.markDeg
  return (
    <PieChart width={320} height={320}>
      <Pie data={model.arcs} dataKey="cents" nameKey="key" cx={160} cy={160} innerRadius={90} outerRadius={130} startAngle={90} endAngle={-270} isAnimationActive={false} stroke="none">
        {model.arcs.map((a) => <Cell key={a.key} fill={a.color} />)}
      </Pie>
      {m !== null && (
        <Pie data={[{ v: 1 }]} dataKey="v" cx={160} cy={160} innerRadius={84} outerRadius={136} startAngle={90 - m + MARK_W / 2} endAngle={90 - m - MARK_W / 2} isAnimationActive={false} stroke="none" fill="#d00000" className="overflow-mark" />
      )}
    </PieChart>
  )
}

function RechartsLines() {
  return (
    <LineChart width={600} height={260} data={series(n)}>
      <XAxis dataKey="d" /><YAxis />
      <Line type="stepAfter" dataKey="income" stroke="#59a14f" isAnimationActive={false} />
      <Line type="stepAfter" dataKey="expenses" stroke="#e15759" isAnimationActive={false} />
    </LineChart>
  )
}

const markPlugin: Plugin<'doughnut'> = {
  id: 'overflowMark',
  afterDatasetsDraw(chart) {
    const m = (chart.options as { markDeg?: number | null }).markDeg
    if (m == null) return
    const a0 = chart.getDatasetMeta(0).data[0] as unknown as { x: number; y: number; innerRadius: number; outerRadius: number }
    const ang = (m - 90) * Math.PI / 180, w = MARK_W * Math.PI / 180
    const ctx = chart.ctx
    ctx.save(); ctx.beginPath(); ctx.strokeStyle = '#d00000'
    ctx.lineWidth = a0.outerRadius - a0.innerRadius + 12
    ctx.arc(a0.x, a0.y, (a0.outerRadius + a0.innerRadius) / 2, ang - w / 2, ang + w / 2); ctx.stroke(); ctx.restore()
    ;(window as unknown as Record<string, unknown>).__markDrawnDeg = m
  },
}

function ChartjsDonut() {
  if (model.kind === 'empty') return <Empty />
  return (
    <div style={{ width: 320, height: 320 }}>
      <Doughnut
        ref={(ch) => { (window as unknown as Record<string, unknown>).__chart = ch }}
        data={{ labels: model.arcs.map((a) => a.key), datasets: [{ data: model.arcs.map((a) => a.cents), backgroundColor: model.arcs.map((a) => a.color), borderWidth: 0 }] }}
        options={{ animation: false, cutout: '70%', responsive: true, maintainAspectRatio: false, markDeg: model.markDeg } as never}
        plugins={[markPlugin]}
      />
    </div>
  )
}

function ChartjsLines() {
  const s = series(n)
  return <div style={{ width: 600, height: 260 }}><CjLine data={{ labels: s.map((p) => p.d), datasets: [{ data: s.map((p) => p.income), stepped: 'after', borderColor: '#59a14f' }, { data: s.map((p) => p.expenses), stepped: 'after', borderColor: '#e15759' }] }} options={{ animation: false }} /></div>
}

export function svgArcs(m: typeof model) {
  if (m.kind === 'empty') return []
  const p = d3pie<{ cents: number }>().value((a) => a.cents).sort(null).startAngle(0).endAngle(2 * Math.PI)
  const g = d3arc<{ startAngle: number; endAngle: number }>().innerRadius(90).outerRadius(130)
  return p(m.arcs).map((s, i) => ({ key: m.arcs[i].key, color: m.arcs[i].color, d: g(s) ?? '', start: s.startAngle, end: s.endAngle }))
}

function SvgDonut() {
  if (model.kind === 'empty') return <Empty />
  const m = model.markDeg, rad = m === null ? 0 : (m * Math.PI) / 180, w = (MARK_W * Math.PI) / 180
  const mark = d3arc<{ startAngle: number; endAngle: number }>().innerRadius(84).outerRadius(136)
  return (
    <svg width={320} height={320} id="svgdonut"><g transform="translate(160,160)">
      {svgArcs(model).map((a) => <path key={a.key} d={a.d} fill={a.color} />)}
      {m !== null && <path className="overflow-mark" data-deg={m} d={mark({ startAngle: rad - w / 2, endAngle: rad + w / 2 }) ?? ''} fill="#d00000" />}
    </g></svg>
  )
}

function RawEmptyPie() { // robustness: Recharts given no data at all
  return <PieChart width={200} height={200}><Pie data={[]} dataKey="cents" innerRadius={50} outerRadius={80} /></PieChart>
}

export default function App() {
  return (
    <div id="chart-root">
      {v === 'a' && <><RechartsDonut /><RechartsLines /></>}
      {v === 'b' && <><ChartjsDonut /><ChartjsLines /></>}
      {v === 'c' && <><SvgDonut /><RechartsLines /></>}
      {v === 'raw-empty' && <><RawEmptyPie /><LineChart width={300} height={200} data={[]}><Line dataKey="x" /></LineChart></>}
    </div>
  )
}
