// Translates the real FastAPI backend's response shapes into the shapes the
// UI components consume. Kept as pure functions in one place so a backend
// field rename only ever costs an edit here, not a hunt through components.

// Backend risk_score is 0-100; every component (pct(), riskColor(), the
// >=.7/>=.45 tier checks) already assumes a 0-1 fraction. Normalize once,
// here, rather than half-converting in a dozen places.
export const fractionFromScore = (score) => Math.max(0, Math.min(1, (score ?? 0) / 100));

// Backend waypoints/GeoPoints are [lng, lat] (GeoJSON-style) or {lat, lng}.
// react-leaflet wants [lat, lng]. Convert once, here.
export function corridorPath(corridor) {
  if (Array.isArray(corridor.waypoints) && corridor.waypoints.length) {
    return corridor.waypoints.map(([lng, lat]) => [lat, lng]);
  }
  const o = corridor.origin, d = corridor.destination;
  if (o && d) return [[o.lat, o.lng], [d.lat, d.lng]];
  return [];
}

// "Strait of Hormuz -> Jamnagar" -> { originLabel: "Strait of Hormuz", destinationLabel: "Jamnagar" }
export function splitCorridorName(name = '') {
  const [originLabel, destinationLabel] = name.split('->').map((s) => s.trim());
  return { originLabel: originLabel || name, destinationLabel: destinationLabel || '' };
}

// GET /corridors row -> the flat shape SupplyChainMap / RiskScoreCard / etc. consume.
export function toUiCorridor(corridor) {
  const { originLabel } = splitCorridorName(corridor.name);
  return {
    id: corridor.id,
    name: corridor.name,
    oil: corridor.crude_grade ? corridor.crude_grade.replace('_', ' ') : corridor.oil_type,
    distance: corridor.distance_km,
    cost: corridor.cost_per_barrel,
    risk: fractionFromScore(corridor.risk_score),
    risk_score: corridor.risk_score ?? 0,
    coords: corridorPath(corridor),
    volume: corridor.current_throughput_bpd ? corridor.current_throughput_bpd / 1_000_000 : 0,
    capacity_bpd: corridor.capacity_bpd,
    current_throughput_bpd: corridor.current_throughput_bpd,
    status: corridor.status || 'active',
    choke_points: corridor.choke_points || [],
    crude_grade: corridor.crude_grade,
    origin: corridor.origin,
    destination: corridor.destination,
    originLabel,
    // Narrative copy the real backend doesn't produce per-corridor at rest --
    // derived from real fields instead of invented text.
    base: corridor.choke_points?.length
      ? `Transits ${corridor.choke_points.join(', ')}`
      : 'No named choke-point exposure',
    event:
      corridor.status === 'disrupted'
        ? 'Closed in current simulation'
        : corridor.risk_score >= 70
        ? 'Elevated signal activity on this corridor'
        : 'No material change in recent signals',
  };
}

// GET /procurement/routes/{id} -> merged onto a ui corridor for the detail card,
// including the real cost breakdown used for RiskScoreCard's factor bars.
export function toUiRouteDetail(detail) {
  const total = detail.landed_cost_per_barrel || 1;
  return {
    ...detail,
    risk: fractionFromScore(detail.risk_score),
    costBreakdown: {
      'crude price': detail.crude_price_per_barrel / total,
      transport: detail.transport_cost_per_barrel / total,
      refining: detail.refining_cost_per_barrel / total,
    },
  };
}

// /procurement/reserves + (optional) the top alternate's cumulative coverage
// from a /scenario/block response -> ReserveGauge's {current, safety, covered}.
export function toUiReserve(reserves, coveragePct) {
  if (!reserves) return { current: 0, safety: 0, covered: 0 };
  const safety = reserves.total_capacity_barrels
    ? (reserves.total_capacity_barrels * 0.15) / reserves.national_daily_consumption_bpd
    : 0;
  return {
    current: Math.round(reserves.days_of_cover * 10) / 10,
    safety: Math.round(safety * 10) / 10,
    covered: coveragePct != null ? Math.round(coveragePct) : 0,
  };
}

// One alternate route from a /scenario/block response -> the row shape
// SupplierRankTable renders.
export function toUiAlternateRow(alt) {
  return {
    id: alt.corridor_id,
    name: alt.name,
    risk: fractionFromScore(alt.risk_score),
    cost: alt.landed_cost_per_barrel,
    etaDays: alt.days_to_supply,
    capacityLabel: `${(alt.spare_capacity_bpd / 1_000_000).toFixed(2)} mb/d spare`,
    suitability: alt.suitability_score,
    coveragePct: alt.coverage?.cumulative_coverage_pct ?? 0,
  };
}

// daily_plan from /scenario/reserve-plan -> the bar-height array DrawdownChart wants (mb/d).
export function toDrawdownSchedule(dailyPlan = []) {
  return dailyPlan.map((d) => d.drawdown_bpd / 1_000_000);
}

// daily_plan -> a scrubber-friendly series (reserve days-of-cover per day),
// used to drive TimelineScrubber off real numbers instead of a fixed fixture.
export function toReserveTimeline(dailyPlan = []) {
  return dailyPlan.map((d) => d.reserve_days_of_cover_after);
}
