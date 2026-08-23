import { useEffect, useMemo, useState } from 'react';
import SupplyChainMap from '../components/digital_twin/SupplyChainMap';
import ScenarioSelector from '../components/scenario/ScenarioSelector';
import CascadeFlowChart from '../components/scenario/CascadeFlowChart';
import SupplierRankTable from '../components/procurement/SupplierRankTable';
import SupplierCompareCard from '../components/procurement/SupplierCompareCard';
import ReserveGauge from '../components/reserves/ReserveGauge';
import DrawdownChart from '../components/reserves/DrawdownChart';
import useSimulation from '../hooks/useSimulation';
import useReserves from '../hooks/useReserves';
import { toDrawdownSchedule, toUiAlternateRow, toUiReserve } from '../utils/adapters';

export default function ScenarioDetail({ routes = [], initialRoute }) {
  const [id, setId] = useState(initialRoute?.id || routes[0]?.id || '');
  const [duration, setDuration] = useState(15);
  const { blockResult, reservePlan, loading, planLoading, error, block, openReservePlan } = useSimulation();
  const { reserves } = useReserves();
  useEffect(() => { if (initialRoute?.id) setId(initialRoute.id); }, [initialRoute?.id]);
  const selected = routes.find((route) => route.id === id) || routes[0];
  const rows = (blockResult?.alternates || []).map(toUiAlternateRow);
  const closed = blockResult?.blocked_corridors?.map((c) => c.id) || [];
  const reserve = toUiReserve(reserves, rows[0]?.coveragePct);
  const advisory = reservePlan?.advisory || blockResult?.advisory;
  const mapRoutes = useMemo(() => routes.map((route) => closed.includes(route.id) ? { ...route, status: 'disrupted', risk: 1 } : route), [routes, closed]);
  const run = () => selected && block({ corridor_ids: [selected.id], top_n: 5, horizon_days: duration });
  return <div className="scenario-page">
    <div className="page-title"><div><p className="eyebrow">WHAT-IF PLANNING</p><h1>Disruption simulation</h1></div><span className="scenario-label">Procurement + reserve model</span></div>
    <div className="simulation-top"><ScenarioSelector routes={routes} route={selected} setRoute={setId} duration={duration} setDuration={setDuration} loading={loading} onRun={run}/><SupplyChainMap routes={mapRoutes} selected={selected} onSelect={(route) => setId(route.id)} closed={closed}/></div>
    {error && <p className="notice">{error}</p>}
    {blockResult?.warning && <p className="notice">{blockResult.warning}</p>}
    {blockResult && <p className="notice">Supply gap: {(blockResult.gap_bpd / 1000000).toFixed(2)} mb/d. Select an alternate to calculate its day-by-day reserve drawdown.</p>}
    {blockResult && <div className="impact-grid"><CascadeFlowChart advisory={advisory}/><ReserveGauge reserve={reserve}/></div>}
    {blockResult && <div className="two-col"><SupplierRankTable rows={rows} onSelect={(row) => openReservePlan(row.id, duration)} selectedId={reservePlan?.alternate_route?.corridor_id} loading={planLoading}/><SupplierCompareCard alternate={reservePlan?.alternate_route || blockResult.alternates?.[0]} advisory={advisory}/></div>}
    {reservePlan && <div className="two-col"><DrawdownChart schedule={toDrawdownSchedule(reservePlan.daily_plan)} /><div className="panel"><p className="eyebrow">RESERVE PLAN SUMMARY</p><p>Route: <b>{reservePlan.alternate_route.name}</b></p><p>Reserve drawdown begins against a {(reservePlan.gap_bpd / 1000000).toFixed(2)} mb/d supply gap and follows the selected route’s {reservePlan.alternate_route.days_to_supply}-day supply lead time.</p></div></div>}
  </div>;
}
