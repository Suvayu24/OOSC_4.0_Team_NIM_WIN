export default function CascadeFlowChart({ advisory }) {
  const text = typeof advisory === 'string' ? advisory : advisory?.summary || advisory?.advisory || 'The backend returned ranked alternates. Select one to produce its strategic-reserve drawdown schedule.';
  return <div className="panel cascade"><p className="eyebrow">SCENARIO ADVISORY</p><p>{text}</p><small>Refining, price and GDP cascade metrics require a dedicated backend endpoint; this screen does not fabricate them.</small></div>;
}
