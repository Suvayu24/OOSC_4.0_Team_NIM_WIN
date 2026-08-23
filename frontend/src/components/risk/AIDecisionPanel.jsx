import { useState } from 'react';

// The backend has no attack-report endpoint. This panel directs the operator
// to the explicit simulation flow, whose outputs are math-backed.
export default function AIDecisionPanel({ route, onSimulate }) {
  const [open, setOpen] = useState(false);
  if (!route) return null;
  const high = route.risk >= 0.7;
  return <div className="panel ai-panel">
    <p className="eyebrow">OPERATOR DECISION SUPPORT</p>
    <div className="ai-head"><strong>{high ? 'HIGH' : 'MONITORED'} PRIORITY</strong><span>Risk engine input</span></div>
    <p>{route.event || route.base}</p>
    <b className="mini-label">Immediate actions</b>
    <ol><li>Validate exposure and cargo nominations.</li><li>Review spare capacity on alternate corridors.</li><li>Prepare strategic-reserve drawdown approval.</li></ol>
    <small>Scenario outputs use the procurement and reserve engines. Advisory is decision support, not an autonomous order.</small>
    <button className="attack-toggle" onClick={() => setOpen(!open)}>{open ? 'Hide action' : 'Model a disruption'}</button>
    {open && <div className="attack-form"><p>Close this corridor in Simulation to rank alternatives and generate a reserve plan.</p><button className="primary" onClick={() => onSimulate?.(route)}>Open simulation</button></div>}
  </div>;
}
