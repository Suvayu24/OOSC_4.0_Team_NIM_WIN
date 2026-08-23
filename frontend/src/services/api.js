// Talks to the real FastAPI backend in /backend (routers.py + procurement_router.py).
// Base URL is configurable via VITE_API_URL so this works against a local
// uvicorn instance in dev or a deployed API later.
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = (import.meta.env.VITE_WS_URL) || API.replace(/^http/, 'ws') + '/ws/risk-updates';

async function request(path, options) {
  const r = await fetch(`${API}${path}`, options);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText} on ${path}`);
  return r.json();
}

const post = (path, body) =>
  request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export const api = {
  // --- Risk engine (routers.py) ---
  corridors: () => request('/corridors'),
  corridor: (id) => request(`/corridors/${id}`),
  seedDemo: () => post('/demo/seed', {}),
  loadTimeline: () => post('/demo/load-timeline', {}),
  advanceClock: (stepHours = 6) => post(`/demo/advance?step_hours=${stepHours}`, {}),

  // --- Adaptive Procurement Orchestrator / Strategic Reserve Agent (procurement_router.py) ---
  seedProcurementDemo: () => post('/procurement/demo/seed', {}),
  routeDetail: (corridorId) => request(`/procurement/routes/${corridorId}`),
  refineries: () => request('/procurement/refineries'),
  reserves: () => request('/procurement/reserves'),

  // body: { corridor_ids?: string[], choke_points?: string[], top_n?: number, horizon_days?: number }
  blockScenario: (body) => post('/procurement/scenario/block', body),

  // body: { corridor_ids?, choke_points?, alternate_corridor_id, horizon_days? }
  reservePlan: (body) => post('/procurement/scenario/reserve-plan', body),
};
