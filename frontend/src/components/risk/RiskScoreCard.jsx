import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { perBbl, pct } from '../../utils/formatters';
import { toUiRouteDetail } from '../../utils/adapters';

// Enriches the selected corridor with GET /procurement/routes/{id} -- the
// real landed-cost breakdown (crude price / transport / refining) and
// days-to-supply. Falls back to just what's already on `route` (from the
// corridor list) if the detail call fails, so the card still renders.
function useRouteDetail(route) {
  const [detail, setDetail] = useState(null);
  useEffect(() => {
    setDetail(null);
    if (!route?.id) return undefined;
    let active = true;
    api
      .routeDetail(route.id)
      .then((d) => {
        if (active && !d.error) setDetail(toUiRouteDetail(d));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [route?.id]);
  return detail;
}

export default function RiskScoreCard({ route }) {
  const detail = useRouteDetail(route);
  if (!route) return <div className="panel empty">Select a corridor on the map.</div>;

  const factors = detail?.costBreakdown && Object.entries(detail.costBreakdown);

  return (
    <div className="panel">
      <p className="eyebrow">CORRIDOR INTELLIGENCE</p>
      <h2>{route.name}</h2>
      <div className="score">
        <strong>{pct(route.risk)}</strong>
        <span>
          risk score
          <br />
          {route.risk >= 0.7 ? 'High exposure' : route.risk >= 0.45 ? 'Elevated' : 'Monitored'}
        </span>
      </div>
      <dl>
        <dt>Crude grade</dt>
        <dd>{route.oil}</dd>
        <dt>Distance</dt>
        <dd>{route.distance?.toLocaleString()} km</dd>
        <dt>{detail ? 'Landed cost /bbl' : 'Crude price /bbl'}</dt>
        <dd>{perBbl(detail ? detail.landed_cost_per_barrel : route.cost)}</dd>
        <dt>Volume exposed</dt>
        <dd>{route.volume?.toFixed?.(2) ?? route.volume} mb/d</dd>
        <dt>{detail ? 'Days to supply' : 'Status'}</dt>
        <dd>{detail ? `${detail.days_to_supply}d` : route.status}</dd>
      </dl>
      {factors && (
        <div className="factor-bars">
          {factors.map(([name, value]) => (
            <div key={name}>
              <span>{name}</span>
              <i>
                <b style={{ width: `${value * 100}%` }} />
              </i>
              <em>{pct(value)}</em>
            </div>
          ))}
        </div>
      )}
      <div className="factor">
        <b>Latest driver</b>
        {route.event || route.base}
      </div>
    </div>
  );
}
