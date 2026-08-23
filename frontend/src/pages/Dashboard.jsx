import { useState } from 'react';
import SupplyChainMap from '../components/digital_twin/SupplyChainMap';
import RiskScoreCard from '../components/risk/RiskScoreCard';
import RiskTrendChart from '../components/risk/RiskTrendChart';
import TriggerEventFeed from '../components/risk/TriggerEventFeed';
import AIDecisionPanel from '../components/risk/AIDecisionPanel';
import useSites from '../hooks/useSites';

export default function Dashboard({ routes, source, history, activity, wsConnected, onSimulate }) {
  const [selected, setSelected] = useState(routes[0]);
  const sites = useSites(routes);

  const merged = routes;
  const active = merged.find((route) => route.id === selected?.id) || merged[0];

  return (
    <div className="dashboard">
      <div className="page-title">
        <div>
          <p className="eyebrow">INDIA CRUDE SUPPLY NETWORK · {routes.length} ROUTES MONITORED</p>
          <h1>Live corridor intelligence</h1>
        </div>
        <span className="updated">
          {source === 'live' ? (wsConnected ? 'Live · connected' : 'Live corridors · updates offline') : 'Demo intelligence'}
        </span>
      </div>
      <div className="stat-row">
        <div>
          <b>{merged.filter((route) => route.risk >= 0.7).length}</b>
          <span>high-risk corridors</span>
        </div>
        <div>
          <b>{merged.reduce((total, route) => total + route.volume, 0).toFixed(1)} mb/d</b>
          <span>volume monitored</span>
        </div>
        <div>
          <b>{routes.length}</b>
          <span>corridors modeled</span>
        </div>
      </div>
      <div className="map-grid">
        <SupplyChainMap routes={merged} sites={sites} selected={active} onSelect={setSelected} closed={active.status === 'disrupted' ? active.id : null} />
        <div className="sidebar-stack">
          <RiskScoreCard route={active} />
          <AIDecisionPanel route={active} onSimulate={onSimulate} />
        </div>
      </div>
      <div className="bottom-grid">
        <RiskTrendChart route={active} history={history?.[active.id]} />
        <TriggerEventFeed routes={merged} activity={activity} />
      </div>
    </div>
  );
}
