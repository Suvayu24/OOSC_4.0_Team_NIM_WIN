export default function RiskTrendChart({ route, history = [] }) {
  const points = history.length ? history : [route?.risk || 0];
  const coords = points.map((risk, i) => `${(i / Math.max(points.length - 1, 1)) * 220},${62 - risk * 52}`).join(' ');
  return <div className="panel chart"><p className="eyebrow">SESSION RISK TREND</p><svg viewBox="0 0 220 70"><polyline fill="none" stroke="#60a5fa" strokeWidth="3" points={coords}/></svg><div className="axis"><span>First reading</span><span>Latest</span></div></div>;
}
