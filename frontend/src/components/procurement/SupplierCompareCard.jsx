export default function SupplierCompareCard({ alternate, advisory }) {
  if (!alternate) return <div className="panel action"><p className="eyebrow">RECOMMENDED ACTION</p><p>Run a disruption scenario to receive ranked procurement options.</p></div>;
  const text = typeof advisory === 'string' ? advisory : advisory?.summary || advisory?.advisory;
  return <div className="panel action"><p className="eyebrow">RECOMMENDED ACTION</p><h3>{alternate.name}</h3><p>Lead time: {alternate.days_to_supply} days · Landed cost: ${alternate.landed_cost_per_barrel?.toFixed?.(2) ?? '—'}/bbl · Risk: {alternate.risk_score ?? '—'}%</p>{text && <p>{text}</p>}<small>Select this route in the table to generate its reserve plan.</small></div>;
}
